"""Himalayas public jobs API (https://himalayas.app/api).

Terms (https://himalayas.app/api, https://himalayas.app/terms#api): use `applicationLink` unchanged for
every Apply button, show a visible link to the job on Himalayas as the source, show jobs only on sites
you operate, do not pass them to other boards/aggregators, and remove jobs once they expire.
Search returns 20 jobs per page; the data refreshes daily.
"""

from __future__ import annotations

import time
from datetime import date
from typing import Any

from ..config import Config
from ..models import Attribution, Job, Salary, make_job_id
from ..text import to_plain_text
from .base import from_epoch, get_json, market_for

API_URL = "https://himalayas.app/jobs/api/search"
NAME = "himalayas"
_PERIODS = {"annual": "yearly", "year": "yearly", "yearly": "yearly", "month": "monthly", "monthly": "monthly",
            "week": "weekly", "day": "daily", "hour": "hourly", "hourly": "hourly"}
_COUNTRY_CODES = {"Peru": "PE", "United States": "US", "Canada": "CA", "Mexico": "MX", "Colombia": "CO",
                  "Chile": "CL", "Argentina": "AR", "Brazil": "BR", "Spain": "ES", "United Kingdom": "GB",
                  "Germany": "DE", "India": "IN"}


def parse(payload: dict, today: date, max_chars: int) -> list[Job]:
    jobs = []
    for item in payload.get("jobs", []):
        guid = item.get("guid")
        if not guid or not item.get("title"):
            continue
        expires = from_epoch(item.get("expiryDate"))
        if expires and expires < today:
            continue  # terms: remove jobs once they expire
        regions = item.get("locationRestrictions") or []
        country = _COUNTRY_CODES.get(regions[0]) if len(regions) == 1 else None
        low, high = item.get("minSalary"), item.get("maxSalary")
        salary = None
        if low or high:
            salary = Salary(min=low or None, max=high or None, currency=item.get("currency"),
                            period=_PERIODS.get((item.get("salaryPeriod") or "").lower()))
        if regions:
            # Peru first when present, so the eligibility check and the UI never lose it to truncation.
            ordered = (["Peru"] if "Peru" in regions else []) + [r for r in regions if r != "Peru"]
            shown = ", ".join(ordered[:6]) + (", …" if len(ordered) > 6 else "")
            location = f"Remote ({shown})"
        else:
            location = "Remote (Worldwide)"
        jobs.append(
            Job(
                id=make_job_id(guid),
                title=item["title"].strip(),
                company=(item.get("companyName") or "Unknown").strip(),
                location=location,
                remote=True,
                country=country,
                salary=salary,
                url=item.get("applicationLink") or guid,
                source=NAME,
                attribution=Attribution(name="Himalayas", url=guid),
                posted_at=from_epoch(item.get("pubDate")),
                expires_at=expires,
                first_seen=today,
                last_seen=today,
                description=to_plain_text(item.get("description"), max_chars),
                market=market_for(country),
            )
        )
    return jobs


def fetch(cfg: Config, session: Any, today: date, *, terms: list[str] | None = None, sleep=time.sleep):
    settings = cfg.sources.himalayas
    jobs: list[Job] = []
    first = True
    for term in terms or cfg.search_terms:
        for page in range(1, settings.pages_per_term + 1):
            if not first:
                sleep(settings.delay_seconds)
            first = False
            payload = get_json(session, API_URL, cfg, {"q": term, "page": page})
            jobs.extend(parse(payload, today, cfg.output.max_description_chars))
            if not payload.get("jobs"):
                break
    return jobs, []
