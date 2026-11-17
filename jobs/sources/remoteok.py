"""Remote OK public API (https://remoteok.com/api).

Terms (first element of the API response): link back (follow, no nofollow) to the job URL on
Remote OK and mention Remote OK as the source; do not use the Remote OK logo. One request returns
the whole current feed, which is filtered locally.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from ..config import Config
from ..models import Attribution, Job, Salary, make_job_id
from ..text import detect_country, to_plain_text
from .base import from_epoch, from_iso, get_json, market_for

API_URL = "https://remoteok.com/api"
NAME = "remoteok"


def parse(payload: list, today: date, max_chars: int) -> list[Job]:
    jobs = []
    for item in payload:
        if not isinstance(item, dict) or "legal" in item or not item.get("position"):
            continue
        url = item.get("url") or item.get("apply_url")
        if not url:
            continue
        region = (item.get("location") or "").strip()
        country = detect_country(region)
        low, high = item.get("salary_min") or 0, item.get("salary_max") or 0
        salary = Salary(min=low or None, max=high or None, currency="USD", period="yearly") if (low or high) else None
        jobs.append(
            Job(
                id=make_job_id(url),
                title=item["position"].strip(),
                company=(item.get("company") or "Unknown").strip(),
                location=f"Remote ({region})" if region else "Remote",
                remote=True,
                country=country,
                salary=salary,
                url=url,
                source=NAME,
                attribution=Attribution(name="Remote OK", url=url),
                posted_at=from_iso(item.get("date")) or from_epoch(item.get("epoch")),
                first_seen=today,
                last_seen=today,
                description=to_plain_text(item.get("description"), max_chars),
                market=market_for(country),
            )
        )
    return jobs


def fetch(cfg: Config, session: Any, today: date, **_: Any):
    payload = get_json(session, API_URL, cfg)
    return parse(payload, today, cfg.output.max_description_chars), []
