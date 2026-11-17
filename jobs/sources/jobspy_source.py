"""JobSpy scraper (python-jobspy): LinkedIn, Indeed, Glassdoor, Google.

Boards rate-limit scrapers aggressively, so `results_wanted` stays small and each site's error is
reported separately instead of failing the run. No attribution is required for these postings.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Callable

from ..config import Config, JobSpySearch
from ..models import Job, Salary, SourceSummary, make_job_id
from ..text import detect_country, to_plain_text
from .base import from_iso, market_for

log = logging.getLogger(__name__)
SITES = ("linkedin", "indeed", "glassdoor", "google")
_PERIODS = {"yearly", "monthly", "weekly", "daily", "hourly"}


def _clean(value: Any) -> Any:
    """Turn pandas NaN/NaT into None."""
    try:
        if value != value:  # NaN
            return None
    except (TypeError, ValueError):
        pass
    return value


def _date(value: Any) -> date | None:
    value = _clean(value)
    if value is None:
        return None
    if isinstance(value, date):
        return value if type(value) is date else value.date()
    return from_iso(value)


def rows_to_jobs(rows: list[dict], search: JobSpySearch, today: date, max_chars: int) -> list[Job]:
    jobs = []
    for raw in rows:
        row = {k: _clean(v) for k, v in raw.items()}
        site, url, title = row.get("site"), row.get("job_url"), row.get("title")
        if site not in SITES or not url or not title:
            continue
        location = (row.get("location") or "").strip()
        text = f"{title} {location}".lower()
        remote = bool(row.get("is_remote")) or "remote" in text or "remoto" in text
        country = detect_country(location) or (search.default_country if not remote else None)
        low, high = row.get("min_amount"), row.get("max_amount")
        salary = None
        if low or high:
            interval = (row.get("interval") or "").lower()
            salary = Salary(min=low or None, max=high or None, currency=row.get("currency"),
                            period=interval if interval in _PERIODS else None)
        jobs.append(
            Job(
                id=make_job_id(url),
                title=str(title).strip(),
                company=(row.get("company") or "Unknown").strip(),
                location=location or ("Remote" if remote else "Unknown"),
                remote=remote,
                country=country,
                salary=salary,
                url=url,
                source=site,
                attribution=None,
                posted_at=_date(row.get("date_posted")),
                first_seen=today,
                last_seen=today,
                description=to_plain_text(row.get("description"), max_chars),
                market=market_for(country),
            )
        )
    return jobs


def _default_scrape(**kwargs: Any):
    from jobspy import scrape_jobs  # imported lazily so tests and other sources do not need it

    return scrape_jobs(**kwargs)


def fetch(cfg: Config, session: Any, today: date, *, scrape: Callable[..., Any] | None = None,
          terms: list[str] | None = None) -> tuple[list[Job], list[SourceSummary]]:
    settings = cfg.sources.jobspy
    scrape = scrape or _default_scrape
    jobs: list[Job] = []
    counts: dict[str, int] = {}
    errors: dict[str, list[str]] = {}
    for search in settings.searches:
        sites = [s for s in search.sites if s in SITES]
        for site in sites:
            counts.setdefault(site, 0)
        for term in terms or cfg.search_terms:
            kwargs: dict[str, Any] = {
                "site_name": sites,
                "search_term": term,
                "location": search.location,
                "is_remote": search.is_remote,
                "results_wanted": settings.results_wanted,
                "hours_old": cfg.hours_old,
                "description_format": "markdown",
                "fetch_description": settings.fetch_description,
                "verbose": 0,
            }
            if search.country_indeed:
                kwargs["country_indeed"] = search.country_indeed
            if "google" in sites:
                kwargs["google_search_term"] = f"{term} jobs {'remote' if search.is_remote else 'in ' + search.location}"
            try:
                frame = scrape(**kwargs)
            except Exception as error:  # one failing call must not stop the others
                message = f"{type(error).__name__}: {error}"
                log.warning("jobspy %s / %r failed: %s", search.name, term, message)
                for site in sites:
                    errors.setdefault(site, []).append(message)
                continue
            for site, message in (getattr(frame, "attrs", {}) or {}).get("errors", {}).items():
                errors.setdefault(str(site), []).append(str(message))
            rows = frame.astype(object).where(frame.notna(), None).to_dict("records") if len(frame) else []
            batch = rows_to_jobs(rows, search, today, cfg.output.max_description_chars)
            for job in batch:
                counts[job.source] = counts.get(job.source, 0) + 1
            jobs.extend(batch)
    summaries = []
    for site, count in counts.items():
        unique = sorted(set(errors.get(site, [])))
        error = "; ".join(unique)[:300] if unique else None
        summaries.append(SourceSummary(name=site, count=count, error=error))
    return jobs, summaries
