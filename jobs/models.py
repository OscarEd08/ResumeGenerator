"""Normalized job model and output envelope (mirrored by src/lib/jobs-schema.ts)."""

from __future__ import annotations

import hashlib
import re
from datetime import date
from typing import Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator

SourceName = Literal["linkedin", "indeed", "glassdoor", "google", "remotive", "remoteok", "himalayas"]
Zone = Literal["apply", "review", "low"]
Market = Literal["peru", "abroad"]
Period = Literal["yearly", "monthly", "weekly", "daily", "hourly"]

# Query parameters that only track the visitor; everything else identifies the posting (e.g. Indeed `jk`).
_TRACKING_PARAMS = {"ref", "refid", "trackingid", "source", "from", "src", "position", "pagenum", "gclid", "fbclid"}


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Salary(_Strict):
    min: float | None = None
    max: float | None = None
    currency: str | None = None
    period: Period | None = None


class Attribution(_Strict):
    """Credit required by a source's API terms: show `name` and link to `url`."""

    name: str
    url: str


class Job(_Strict):
    id: str = Field(pattern=r"^job-[0-9a-f]{8}$")
    title: str
    company: str
    location: str
    remote: bool
    country: str | None = Field(default=None, pattern=r"^[A-Z]{2}$")
    salary: Salary | None = None
    url: str
    source: SourceName
    attribution: Attribution | None = None
    posted_at: date | None = None
    expires_at: date | None = None
    first_seen: date
    last_seen: date
    description: str
    score: int = Field(default=0, ge=0, le=100)
    zone: Zone = "low"
    matched: list[str] = []
    missing: list[str] = []
    reasons: list[str] = []
    market: Market

    @field_validator("title", "company", "location", mode="before")
    @classmethod
    def _clean_inline(cls, value: object) -> object:
        """Drop BOM/zero-width characters and collapse whitespace in one-line fields."""
        if isinstance(value, str):
            value = re.sub(r"[\ufeff\u200b\u200c\u200d\u2060]", "", value)
            value = re.sub(r"\s+", " ", value).strip()
        return value


class SourceSummary(_Strict):
    name: str
    count: int = 0
    error: str | None = None

    def dump(self) -> dict:
        return self.model_dump(exclude_none=True)


class JobsFile(_Strict):
    generated_at: str
    sources: list[SourceSummary]
    jobs: list[Job]


def canonical_url(url: str) -> str:
    """Lowercase scheme/host, drop fragment, tracking params and trailing slash; sort remaining params."""
    parts = urlsplit(url.strip())
    query = sorted(
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=False)
        if not k.lower().startswith("utm_") and k.lower() not in _TRACKING_PARAMS
    )
    path = parts.path.rstrip("/") or ""
    return urlunsplit((parts.scheme.lower() or "https", parts.netloc.lower(), path, urlencode(query), ""))


def make_job_id(url: str) -> str:
    return "job-" + hashlib.sha1(canonical_url(url).encode("utf-8")).hexdigest()[:8]
