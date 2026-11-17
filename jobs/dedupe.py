"""Deduplicate postings within a run and against the previous data/jobs.json."""

from __future__ import annotations

import re
import unicodedata
from datetime import date, timedelta

from .models import Job, canonical_url

_COMPANY_SUFFIXES = re.compile(
    r"\b(inc|llc|ltd|limited|corp|corporation|co|gmbh|s\.?a\.?c?|s\.?r\.?l|sas|bv|plc|pty|company)\b\.?"
)
_TITLE_NOISE = re.compile(r"\((?:[^)]*remote[^)]*|[^)]*remoto[^)]*|[^)]*hybrid[^)]*)\)|[-–|]\s*(remote|remoto|hybrid)\b.*$")


def _fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()
    return text


def normalize_company(company: str) -> str:
    text = _COMPANY_SUFFIXES.sub(" ", _fold(company))
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def normalize_title(title: str) -> str:
    text = _TITLE_NOISE.sub(" ", _fold(title))
    return re.sub(r"[^a-z0-9#+.]+", " ", text).strip()


def _keys(job: Job) -> tuple[str, str]:
    return canonical_url(job.url), f"{normalize_company(job.company)}|{normalize_title(job.title)}"


def _better(current: Job, incoming: Job, priority: list[str]) -> Job:
    """Pick the richer posting; on ties prefer the source listed first in `priority`, then the incoming one."""
    def rank(job: Job) -> tuple[int, int]:
        order = priority.index(job.source) if job.source in priority else len(priority)
        return (len(job.description) // 200, -order)

    return incoming if rank(incoming) >= rank(current) else current


def merge(previous: list[Job], fresh: list[Job], priority: list[str]) -> list[Job]:
    """Merge fresh postings into previous ones.

    Duplicates share a canonical URL or a normalized (company, title). The merged record keeps the
    earliest `first_seen`, the latest `last_seen`, and the id of the oldest record so links stay stable.
    """
    merged: list[Job] = []
    by_url: dict[str, int] = {}
    by_name: dict[str, int] = {}

    def add(job: Job) -> None:
        url_key, name_key = _keys(job)
        index = by_url.get(url_key, by_name.get(name_key))
        if index is None:
            merged.append(job)
            index = len(merged) - 1
        else:
            current = merged[index]
            winner = _better(current, job, priority)
            merged[index] = winner.model_copy(update={
                "id": current.id,
                "first_seen": min(current.first_seen, job.first_seen),
                "last_seen": max(current.last_seen, job.last_seen),
            })
        by_url.setdefault(url_key, index)
        by_name.setdefault(name_key, index)
        for key in _keys(merged[index]):
            (by_url if key.startswith("http") else by_name).setdefault(key, index)

    for job in previous:
        add(job)
    for job in fresh:
        add(job)
    return merged


def prune(jobs: list[Job], today: date, days: int) -> list[Job]:
    """Drop postings not seen for more than `days` days and postings past their expiry date."""
    cutoff = today - timedelta(days=days)
    return [j for j in jobs if j.last_seen >= cutoff and not (j.expires_at and j.expires_at < today)]
