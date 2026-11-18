"""Cover letter rendering: one page in the CV's typeface and header (Typst -> PDF).

`cv/tailor.py letter <job-id>` validates the letter text and calls `render()`; this module only lays it out.
The PDF is a plain text layer (no tables, no images) so applicant tracking systems read it in order.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import rendercv_fonts
import typst

FONT_DIR = Path(rendercv_fonts.__file__).parent

MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
           "November", "December"],
    "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
           "noviembre", "diciembre"],
}
LABELS = {
    "en": {"team": "Hiring Team", "role": "Re:"},
    "es": {"team": "Equipo de selección", "role": "Ref.:"},
}


def letter_date(day: date, lang: str) -> str:
    month = MONTHS[lang][day.month - 1]
    return f"{month} {day.day}, {day.year}" if lang == "en" else f"{day.day} de {month} de {day.year}"


def format_phone(phone: str) -> str:
    """'+51964407956' -> '+51 964 407 956' (the CV header's international format for Peru numbers)."""
    match = re.fullmatch(r"\+51(\d{3})(\d{3})(\d{3})", phone)
    return f"+51 {match[1]} {match[2]} {match[3]}" if match else phone


def contact_line(cv: dict) -> str:
    parts = [cv.get("location"), format_phone(str(cv["phone"])) if cv.get("phone") else None, cv.get("email")]
    for network in cv.get("social_networks") or []:
        if network.get("network") == "LinkedIn":
            parts.append(f"linkedin.com/in/{network['username']}")
    return "  ·  ".join(part for part in parts if part)


def _str(text: str) -> str:
    """A Typst string literal: shown verbatim, so `*`, `_`, `#`, `@` and `$` in the letter stay plain text."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def typst_source(cv: dict, job: dict, letter: dict, lang: str, day: date) -> str:
    labels = LABELS[lang]
    paragraphs = "\n\n".join(f"#{_str(p)}" for p in letter["paragraphs"])
    return f"""#set page(paper: "us-letter", margin: (x: 0.75in, top: 0.6in, bottom: 0.6in))
#set text(font: "XCharter", size: 10.75pt, lang: "{lang}")
#set par(justify: false, leading: 0.62em, spacing: 1.05em)

#text(size: 25pt, weight: "bold", {_str(cv["name"])})
#v(0.05cm)
#text(size: 10pt, weight: "bold", {_str(cv.get("headline", ""))})
#v(-0.1cm)
#text(size: 10pt, {_str(contact_line(cv))})
#v(-0.25cm)
#line(length: 100%, stroke: 0.5pt)
#v(0.35cm)

#{_str(letter_date(day, lang))}

#{_str(labels["team"])} \\
#{_str(job["company"])} \\
#{_str(labels["role"] + " " + job["title"])}

#v(0.15cm)
#{_str(letter["greeting"])}

{paragraphs}

#{_str(letter["closing"])} \\
#{_str(cv["name"])}
"""


def render(cv: dict, job: dict, letter: dict, lang: str, out_pdf: Path, day: date | None = None) -> Path:
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    source = typst_source(cv, job, letter, lang, day or date.today())
    typst.compile(source.encode("utf-8"), output=str(out_pdf), font_paths=[str(FONT_DIR)])
    return out_pdf
