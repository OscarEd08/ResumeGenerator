"""Typed loader for `jobs/config.yaml`."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = Path(__file__).resolve().parent / "config.yaml"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class JobSpySearch(_Strict):
    name: str
    sites: list[str]
    location: str
    country_indeed: str | None = None
    is_remote: bool = False
    default_country: str | None = None


class JobSpyConfig(_Strict):
    enabled: bool = True
    results_wanted: int = 15
    fetch_description: bool = True
    searches: list[JobSpySearch]


class RemotiveConfig(_Strict):
    enabled: bool = True
    limit_per_term: int = 30
    delay_seconds: float = 31


class RemoteOKConfig(_Strict):
    enabled: bool = True


class HimalayasConfig(_Strict):
    enabled: bool = True
    pages_per_term: int = 1
    delay_seconds: float = 2


class SourcesConfig(_Strict):
    jobspy: JobSpyConfig
    remotive: RemotiveConfig
    remoteok: RemoteOKConfig
    himalayas: HimalayasConfig


class FiltersConfig(_Strict):
    title_must_match_any: list[str]
    exclude_title_keywords: list[str]
    exclude_title_stacks_without_core: list[str]
    onsite_countries: list[str]


class Zones(_Strict):
    apply: int = 85
    review: int = 70


class Adjustments(_Strict):
    remote_abroad_bonus: float = 5
    peru_bonus: float = 0
    region_restricted_penalty: float = 25
    too_senior_penalty: float = 20
    junior_penalty: float = 5
    years_penalty: float = 10
    exclusion_penalty: float = 40


class Seniority(_Strict):
    too_senior_title: list[str]
    junior_title: list[str]
    max_years_required: int = 6


class ScoringConfig(_Strict):
    zones: Zones
    min_score_to_keep: int = 35
    coverage_weight: float = 70
    core_weight: float = 30
    core_terms: dict[str, float]
    title_term_weight: float = 3
    description_term_weight: float = 1
    nice_to_have_weight: float = 0.5
    min_evidence_weight: float = 6
    skills_min_strength: float = 0.6
    profile_saturation: int = 8
    adjustments: Adjustments
    eligible_regions: list[str]
    seniority: Seniority
    exclusion_keywords: list[str]


class OutputConfig(_Strict):
    path: str = "data/jobs.json"
    prune_after_days: int = 30
    max_description_chars: int = 4000


class Config(_Strict):
    search_terms: list[str] = Field(min_length=1)
    hours_old: int = 72
    user_agent: str
    request_timeout_seconds: float = 30
    sources: SourcesConfig
    filters: FiltersConfig
    scoring: ScoringConfig
    output: OutputConfig
    synonyms: dict[str, list[str]]
    labels: dict[str, str] = {}
    source_priority: list[str] = []

    def label(self, term: str) -> str:
        return self.labels.get(term, term)


def load_config(path: Path = DEFAULT_CONFIG) -> Config:
    return Config.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
