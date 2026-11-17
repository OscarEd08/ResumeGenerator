"""Render a RenderCV YAML file to PDF + PNG pages.

Usage:
    python cv/build.py <input.yaml> [--out <dir>]

Outputs `<stem>.pdf` and `<stem>_<page>.png` into --out (default: public/cv/).
The Typst intermediate is written to a temporary directory and discarded;
Markdown and HTML outputs are not generated.

The module also holds the ATS text-layer checks (`ats_problems`) that cv/tests/test_ats.py
and cv/tailor.py run against a rendered PDF.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pypdf

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "public" / "cv"


def utf8_env() -> dict[str, str]:
    """RenderCV crashes on Windows cp1252 consoles unless Python runs in UTF-8 mode."""
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def build(input_yaml: Path, out_dir: Path) -> list[Path]:
    input_yaml = input_yaml.resolve()
    if not input_yaml.is_file():
        raise FileNotFoundError(f"Input file not found: {input_yaml}")
    stem = input_yaml.stem
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="rendercv_") as tmp:
        tmp_dir = Path(tmp)
        command = [
            sys.executable, "-m", "rendercv", "render", str(input_yaml),
            "--typst-path", str(tmp_dir / f"{stem}.typ"),
            "--pdf-path", str(tmp_dir / f"{stem}.pdf"),
            "--png-path", str(tmp_dir / f"{stem}.png"),
            "--dont-generate-markdown",
            "--dont-generate-html",
            "--quiet",
        ]
        result = subprocess.run(
            command, env=utf8_env(), capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        pdf = tmp_dir / f"{stem}.pdf"
        if result.returncode != 0 or not pdf.is_file():
            raise RuntimeError(
                f"RenderCV failed (exit {result.returncode}):\n{result.stdout}\n{result.stderr}"
            )

        return publish([pdf, *sorted(tmp_dir.glob(f"{stem}_*.png"))], out_dir, stem)


def publish(files: list[Path], out_dir: Path, stem: str) -> list[Path]:
    """Copy one CV's rendered files into out_dir, removing its stale outputs (e.g. a page that no longer exists)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in [out_dir / f"{stem}.pdf", *out_dir.glob(f"{stem}_*.png")]:
        old.unlink(missing_ok=True)
    return [Path(shutil.copy2(path, out_dir / path.name)) for path in files]


# --- ATS text-layer checks (shared by cv/tests/test_ats.py and cv/tailor.py) ------------------
#
# The PDF text is extracted with pypdf (a reasonable proxy for what ATS parsers see) and compared
# against the RenderCV source, so the checks follow the content automatically. Each check returns
# a list of problems; an empty list means it passed.

INVISIBLE = dict.fromkeys(map(ord, "​‌‍﻿"), None)
QUOTES = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'})

# RenderCV 2.8 month abbreviations per locale language (rendercv/schema/models/locale).
MONTH_ABBREVIATIONS = {
    "english": ["Jan", "Feb", "Mar", "Apr", "May", "June", "July", "Aug", "Sept", "Oct", "Nov", "Dec"],
    "spanish": ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
}


def normalize(text: str) -> str:
    """Collapse whitespace/line breaks, unify quotes and drop markdown markers."""
    text = str(text).translate(INVISIBLE).translate(QUOTES)
    text = text.replace("**", "").replace("*", "")
    return re.sub(r"\s+", " ", text).strip()


def format_date(value, locale: dict | None = None) -> str:
    locale = locale or {}
    if value is None:
        return ""
    if str(value).lower() == "present":
        return locale.get("present", "present")
    text = str(value)
    if re.fullmatch(r"\d{4}", text):
        return text
    year, month = text.split("-")[:2]
    months = locale.get("month_abbreviations") or MONTH_ABBREVIATIONS[locale.get("language", "english")]
    return f"{months[int(month) - 1]} {year}"


def entry_date(entry: dict, locale: dict | None = None) -> str:
    if entry.get("date"):
        return str(entry["date"])
    return f"{format_date(entry.get('start_date'), locale)} - {format_date(entry.get('end_date'), locale)}"


def pdf_text(pdf: Path) -> str:
    reader = pypdf.PdfReader(pdf)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def check_name_is_first_line(raw_text: str, cv: dict) -> list[str]:
    first_line = next((line for line in raw_text.splitlines() if line.strip()), "")
    return [] if normalize(first_line) == cv["name"] else [f"first line is {first_line!r}, expected the name"]


def check_headline_and_email(text: str, cv: dict) -> list[str]:
    expected = [normalize(cv[key]) for key in ("headline", "email") if cv.get(key)]
    return [f"missing {value!r}" for value in expected if value not in text]


def check_section_headings_in_order(text: str, cv: dict) -> list[str]:
    titles = [normalize(t) for t in cv["sections"] if normalize(t)]
    positions = [text.find(t) for t in titles]
    if any(p < 0 for p in positions) or positions != sorted(positions):
        return [f"section headings missing or out of order: {dict(zip(titles, positions))}"]
    return []


def check_entries_read_company_position_dates(text: str, cv: dict, locale: dict | None = None) -> list[str]:
    problems, cursor = [], 0
    for section in cv["sections"].values():
        for entry in section:
            if not isinstance(entry, dict) or "company" not in entry:
                continue
            company = text.find(normalize(entry["company"]), cursor)
            position = text.find(normalize(entry["position"]), company)
            dates = text.find(entry_date(entry, locale), position)
            if not -1 < company < position < dates:
                problems.append(f"{entry['company']}: company/position/dates out of reading order "
                                f"({company}, {position}, {dates})")
                continue
            cursor = dates
    return problems


def check_every_highlight_present(text: str, cv: dict) -> list[str]:
    return [
        f"bullet not found in reading order: {highlight!r}"
        for section in cv["sections"].values()
        for entry in section
        if isinstance(entry, dict)
        for highlight in entry.get("highlights") or []
        if normalize(highlight) not in text
    ]


def check_text_entries_and_skills_present(text: str, cv: dict) -> list[str]:
    problems = []
    for section in cv["sections"].values():
        for entry in section:
            if isinstance(entry, str):
                expected = normalize(entry)
            elif "label" in entry:
                expected = normalize(f"{entry['label']}: {entry['details']}")
            else:
                continue
            if expected not in text:
                problems.append(f"text not found: {expected!r}")
    return problems


def check_no_last_updated_note(text: str) -> list[str]:
    return ["a 'last updated' note is printed"] if "last updated" in text.lower() else []


def check_real_characters(raw_text: str) -> list[str]:
    return [f"text layer contains {bad!r}" for bad in ("�", "(cid:") if bad in raw_text]


def ats_problems(pdf: Path, cv: dict, locale: dict | None = None) -> list[str]:
    """Every ATS check above against one rendered PDF and its RenderCV `cv` source."""
    raw = pdf_text(pdf)
    text = normalize(raw)
    return [
        *check_name_is_first_line(raw, cv),
        *check_headline_and_email(text, cv),
        *check_section_headings_in_order(text, cv),
        *check_entries_read_company_position_dates(text, cv, locale),
        *check_every_highlight_present(text, cv),
        *check_text_entries_and_skills_present(text, cv),
        *check_no_last_updated_note(text),
        *check_real_characters(raw),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a RenderCV YAML file to PDF + PNG.")
    parser.add_argument("input", type=Path, help="RenderCV YAML input file")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"output directory (default: {DEFAULT_OUT})")
    args = parser.parse_args(argv)
    try:
        files = build(args.input, args.out)
    except (FileNotFoundError, RuntimeError) as error:
        print(error, file=sys.stderr)
        return 1
    for path in files:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
