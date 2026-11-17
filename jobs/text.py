"""Text helpers: HTML/Markdown to plain text, country and salary parsing."""

from __future__ import annotations

import html
import re

from .models import Salary

_BLOCK_TAGS = re.compile(r"</?(p|div|br|li|ul|ol|h[1-6]|tr|section)\b[^>]*>", re.I)
_TAGS = re.compile(r"<[^>]+>")
_MD_MARKS = re.compile(r"(\*\*|__|`|^#{1,6}\s*|^\s*[*-]\s+)", re.M)


def to_plain_text(raw: str | None, max_chars: int) -> str:
    """Strip HTML tags and light Markdown, keep line breaks, collapse spaces, trim to max_chars."""
    if not raw:
        return ""
    text = _BLOCK_TAGS.sub("\n", raw)
    text = _TAGS.sub("", text)
    text = html.unescape(text)
    text = _MD_MARKS.sub("", text)
    text = text.replace("\\-", "-").replace("\\.", ".").replace("\\#", "#").replace("\\+", "+")
    lines = [re.sub(r"[ \t ]+", " ", line).strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    if len(text) > max_chars:
        text = text[: max_chars - 1].rsplit(" ", 1)[0] + "…"
    return text


# Country names/codes recognised in free-text locations (ISO-2).
_COUNTRIES = {
    "peru": "PE", "perú": "PE", "lima": "PE",
    "united states": "US", "usa": "US", "u.s.": "US",
    "canada": "CA", "mexico": "MX", "méxico": "MX", "colombia": "CO", "chile": "CL", "argentina": "AR",
    "brazil": "BR", "brasil": "BR", "ecuador": "EC", "uruguay": "UY", "spain": "ES", "españa": "ES",
    "united kingdom": "GB", "uk": "GB", "germany": "DE", "netherlands": "NL", "portugal": "PT",
    "poland": "PL", "ireland": "IE", "france": "FR", "india": "IN",
}
_US_STATES = set(
    "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND "
    "OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC".split()
)
_ISO2 = set(_COUNTRIES.values())


_HYBRID = re.compile(r"\bh[ií]brid[oa]?\b|\bhybrid\b", re.I)
_RELOCATION = re.compile(
    r"\b(?:relocat\w*|reubicaci[oó]n|relocalizaci[oó]n|visa sponsorship)", re.I)
_NO_RELOCATION = re.compile(
    r"\b(?:no|not|without|unable to (?:offer|provide)|cannot (?:offer|provide)|sin)\b[^.\n]{0,40}"
    r"(?:relocat\w*|reubicaci[oó]n|relocalizaci[oó]n|visa sponsorship)"
    r"|(?:relocat\w*|visa sponsorship)[^.\n]{0,30}\b(?:not (?:available|offered|provided)|unavailable)\b", re.I)


def work_mode(title: str, location: str, description: str, remote: bool) -> str:
    """Classify a posting as "remote", "hybrid" or "onsite".

    A hybrid mention in the title or location wins over the remote flag (sources set it from loose
    text matches); a hybrid mention only in the description applies to non-remote postings.
    """
    if _HYBRID.search(f"{title} {location}"):
        return "hybrid"
    if remote:
        return "remote"
    return "hybrid" if _HYBRID.search(description) else "onsite"


def offers_relocation(text: str) -> bool:
    """True when the posting offers relocation or visa sponsorship (and does not say it does not)."""
    return bool(_RELOCATION.search(text)) and not _NO_RELOCATION.search(text)


def detect_country(location: str | None) -> str | None:
    """Best-effort ISO-2 country from a location string; None when unknown or multi-country."""
    if not location:
        return None
    low = location.lower()
    found = {code for name, code in _COUNTRIES.items() if re.search(rf"(?<![a-z]){re.escape(name)}(?![a-z])", low)}
    if len(found) == 1:
        return found.pop()
    if found:
        return None
    parts = [p.strip() for p in location.split(",")]
    last = parts[-1] if parts else ""
    if last.upper() in _ISO2 and len(last) == 2:
        return last.upper()
    if last.upper() == "US" or (len(parts) >= 2 and last.upper() in _US_STATES and len(last) == 2):
        return "US"
    return None


_SALARY_NUM = re.compile(r"(\d+(?:[.,]\d+)?)\s*(k)?", re.I)
_CURRENCY = {"$": "USD", "usd": "USD", "€": "EUR", "eur": "EUR", "£": "GBP", "gbp": "GBP", "s/": "PEN", "pen": "PEN"}


def parse_salary_text(text: str | None) -> Salary | None:
    """Parse simple ranges like "$60k - $80k" or "USD 4000/month". Returns None when unclear."""
    if not text or not text.strip():
        return None
    low = text.lower()
    currency = next((code for mark, code in _CURRENCY.items() if mark in low), None)
    values = []
    for number, kilo in _SALARY_NUM.findall(low):
        value = float(number.replace(",", "")) if "," in number and len(number.split(",")[-1]) == 3 else float(number.replace(",", "."))
        values.append(value * 1000 if kilo else value)
    values = [v for v in values if v >= 10]
    if not values:
        return None
    if "hour" in low or "/hr" in low:
        period = "hourly"
    elif "month" in low or "/mo" in low:
        period = "monthly"
    elif max(values) >= 10000 or "year" in low or "annual" in low:
        period = "yearly"
    else:
        period = None
    return Salary(min=min(values), max=max(values) if len(values) > 1 else None, currency=currency, period=period)
