"""ATS checks: build cv/base.yaml and verify the PDF text layer reads in a logical order.

The checks themselves live in cv/build.py (`check_*`, `ats_problems`) so cv/tailor.py runs the
same ones on every tailored CV. The text is extracted with pypdf (a reasonable proxy for what ATS
parsers see) and compared against the YAML source, so the test follows the content automatically.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from ruamel.yaml import YAML

import build

CV_DIR = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = CV_DIR / "build.py"
BASE_YAML = CV_DIR / "base.yaml"


@pytest.fixture(scope="module")
def base_source() -> dict:
    return YAML(typ="safe").load(BASE_YAML.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def cv_source(base_source):
    return base_source["cv"]


@pytest.fixture(scope="module")
def locale(base_source):
    return base_source.get("locale")


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
    return build.pdf_text(pdf_path)


@pytest.fixture(scope="module")
def text(raw_text) -> str:
    return build.normalize(raw_text)


def test_build_outputs_only_pdf_and_png(pdf_path):
    produced = sorted(p.suffix for p in pdf_path.parent.iterdir())
    assert set(produced) == {".pdf", ".png"}, produced


def test_name_is_first_line(raw_text, cv_source):
    assert build.check_name_is_first_line(raw_text, cv_source) == []


def test_headline_and_email_present(text, cv_source):
    assert cv_source["email"]
    assert build.check_headline_and_email(text, cv_source) == []


def test_section_headings_in_order(text, cv_source):
    assert build.check_section_headings_in_order(text, cv_source) == []


def test_experience_entries_read_company_position_dates(text, cv_source, locale):
    assert build.check_entries_read_company_position_dates(text, cv_source, locale) == []


def test_every_highlight_present(text, cv_source):
    assert build.check_every_highlight_present(text, cv_source) == []


def test_text_entries_and_skills_present(text, cv_source):
    assert build.check_text_entries_and_skills_present(text, cv_source) == []


def test_no_last_updated_note(text):
    assert build.check_no_last_updated_note(text) == []


def test_text_uses_real_characters(raw_text):
    assert build.check_real_characters(raw_text) == []


def test_ats_problems_aggregates_every_check(pdf_path, cv_source, locale):
    assert build.ats_problems(pdf_path, cv_source, locale) == []


def test_date_formatting_follows_the_locale():
    assert build.entry_date({"start_date": "2024-06", "end_date": "present"}, {"present": "Present"}) == "June 2024 - Present"
    spanish = {"language": "spanish", "present": "Presente"}
    assert build.entry_date({"start_date": "2024-01", "end_date": "2024-12"}, spanish) == "Ene 2024 - Dic 2024"
    assert build.entry_date({"date": "2020 - 2024"}) == "2020 - 2024"


def test_bullet_split_by_a_line_break_at_a_hyphen_is_still_found():
    # pypdf extracts "image-to-PDF" broken across lines as "image-to- PDF" and Typst hyphenation as "creden- tials".
    cv = {"sections": {"experience": [{"highlights": ["Built an image-to-PDF service for credentials and e-mail."]}]}}
    text = build.normalize("Built an image-to-\nPDF service for creden-\ntials and e-\nmail.")
    assert build.check_every_highlight_present(text, cv) == []
    assert build.check_every_highlight_present(build.normalize("Built a PDF service."), cv) != []
