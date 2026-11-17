"""Remotive public API (https://remotive.com/api/remote-jobs).

Terms (https://github.com/remotive-com/remote-jobs-api): link back to the job URL on Remotive and
mention Remotive as the source; at most ~4 calls a day and never more than 2 per minute.
"""

from __future__ import annotations

import time
from datetime import date
from typing import Any

from ..config import Config
from ..models import Attribution, Job, make_job_id
from ..text import detect_country, parse_salary_text, to_plain_text
from .base import from_iso, get_json, market_for

API_URL = "https://remotive.com/api/remote-jobs"
NAME = "remotive"


def parse(payload: dict, today: date, max_chars: int) -> list[Job]:
    jobs = []
    for item in payload.get("jobs", []):
        url = item.get("url")
        if not url or not item.get("title"):
            continue
        region = (item.get("candidate_required_location") or "").strip()
        country = detect_country(region)
        jobs.append(
            Job(
                id=make_job_id(url),
                title=item["title"].strip(),
                company=(item.get("company_name") or "Unknown").strip(),
                location=f"Remote ({region})" if region else "Remote",
                remote=True,
                country=country,
                salary=parse_salary_text(item.get("salary")),
                url=url,
                source=NAME,
                attribution=Attribution(name="Remotive", url=url),
                posted_at=from_iso(item.get("publication_date")),
                first_seen=today,
                last_seen=today,
                description=to_plain_text(item.get("description"), max_chars),
                market=market_for(country),
            )
        )
    return jobs


def fetch(cfg: Config, session: Any, today: date, *, terms: list[str] | None = None, sleep=time.sleep):
    settings = cfg.sources.remotive
    jobs: list[Job] = []
    for index, term in enumerate(terms or cfg.search_terms):
        if index:
            sleep(settings.delay_seconds)  # Remotive blocks more than 2 requests per minute
        payload = get_json(session, API_URL, cfg, {"search": term, "limit": settings.limit_per_term})
        jobs.extend(parse(payload, today, cfg.output.max_description_chars))
    return jobs, []
