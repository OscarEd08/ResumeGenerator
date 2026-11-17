"""ATS checks: build cv/base.yaml and verify the PDF text layer reads in a logical order.

The text is extracted with pypdf (a reasonable proxy for what ATS parsers see) and
compared against the YAML source, so the test follows the content automatically.
"""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import pypdf
import pytest
from ruamel.yaml import YAML

CV_DIR = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = CV_DIR / "build.py"
BASE_YAML = CV_DIR / "base.yaml"

INVISIBLE = dict.fromkeys(map(ord, "​‌‍﻿"), None)
QUOTES = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'})


def normalize(text: str) -> str:
    """Collapse whitespace/line breaks, unify quotes and drop markdown markers."""
    text = str(text).translate(INVISIBLE).translate(QUOTES)
    text = text.replace("**", "").replace("*", "")
    return re.sub(r"\s+", " ", text).strip()


def format_date(value) -> str:
    if value is None:
        return ""
    if str(value).lower() == "present":
        return "Present"
    text = str(value)
    if re.fullmatch(r"\d{4}", text):
        return text
    parsed = date.fromisoformat(text if len(text) > 7 else f"{text}-01")
    return parsed.strftime("%b %Y")


def entry_date(entry) -> str:
    if entry.get("date"):
        return str(entry["date"])
    return f"{format_date(entry.get('start_date'))} - {format_date(entry.get('end_date'))}"


@pytest.fixture(scope="module")
def cv_source():
    return YAML(typ="safe").load(BASE_YAML.read_text(encoding="utf-8"))["cv"]


@pytest.fixture(scope="module")
def pdf_path(tmp_path_factory) -> Path:
    out_dir = tmp_path_factory.mktemp("cv_build")
    result = subprocess.run(
        [sys.executable, str(BUILD_SCRIPT), str(BASE_YAML), "--out", str(out_dir)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    pdf = out_dir / "base.pdf"
    assert pdf.is_file(), f"build did not produce {pdf}"
    return pdf


@pytest.fixture(scope="module")
def raw_text(pdf_path) -> str:
    reader = pypdf.PdfReader(pdf_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


@pytest.fixture(scope="module")
def text(raw_text) -> str:
    return normalize(raw_text)


def test_build_outputs_only_pdf_and_png(pdf_path):
    produced = sorted(p.suffix for p in pdf_path.parent.iterdir())
    assert set(produced) == {".pdf", ".png"}, produced


def test_name_is_first_line(raw_text, cv_source):
    first_line = next(line for line in raw_text.splitlines() if line.strip())
    assert normalize(first_line) == cv_source["name"]


def test_headline_and_email_present(text, cv_source):
    assert normalize(cv_source["headline"]) in text
    assert cv_source["email"] in text


def test_section_headings_in_order(text, cv_source):
    titles = [t for t in cv_source["sections"] if normalize(t)]
    positions = [text.find(normalize(t)) for t in titles]
    assert all(p >= 0 for p in positions), dict(zip(titles, positions))
    assert positions == sorted(positions), dict(zip(titles, positions))


def test_experience_entries_read_company_position_dates(text, cv_source):
    cursor = 0
    for section in cv_source["sections"].values():
        for entry in section:
            if not isinstance(entry, dict) or "company" not in entry:
                continue
            company = text.find(normalize(entry["company"]), cursor)
            position = text.find(normalize(entry["position"]), company)
            dates = text.find(entry_date(entry), position)
            assert -1 < company < position < dates, (entry["company"], company, position, dates)
            cursor = dates


def test_every_highlight_present(text, cv_source):
    missing = [
        highlight
        for section in cv_source["sections"].values()
        for entry in section
        if isinstance(entry, dict)
        for highlight in entry.get("highlights") or []
        if normalize(highlight) not in text
    ]
    assert not missing


def test_text_entries_and_skills_present(text, cv_source):
    for section in cv_source["sections"].values():
        for entry in section:
            if isinstance(entry, str):
                assert normalize(entry) in text
            elif "label" in entry:
                assert normalize(f"{entry['label']}: {entry['details']}") in text


def test_no_last_updated_note(text):
    assert "last updated" not in text.lower()


def test_text_uses_real_characters(raw_text):
    assert "�" not in raw_text
    assert "(cid:" not in raw_text
