"""Stage 1 rule filters and stage 2 deterministic scoring against the profile bank.

Score = coverage_weight * coverage + core_weight * core + adjustments, clamped to 0..100.

- coverage: share of the posting's tech terms (weighted: title > description > nice-to-have) that the
  profile has, each matched term scaled by how strongly the profile backs it; scaled down for thin
  postings whose total term weight is below `min_evidence_weight`.
- core: how much of the configured core stack (.NET, C#, Azure, Angular, SQL Server) the posting asks for.
- adjustments: remote-abroad bonus, region restriction, seniority, years required, exclusion keywords.
"""

from __future__ import annotations

import math
import re
from functools import lru_cache

from .config import Config
from .models import Job
from .text import offers_relocation, work_mode

_NICE_HEADER = re.compile(
    r"(nice[- ]to[- ]have|bonus|preferred|a plus|is a plus|deseable|valorable|plus:|good to have|desirable)", re.I
)
# "5+ years of experience", "3-5 years professional .NET experience", "8 años de experiencia".
_YEARS = re.compile(
    r"(\d{1,2})\s*\+?\s*(?:-\s*\d{1,2}\s*\+?\s*)?(?:years?|yrs?|años)\s+(?:of\s+|de\s+)?"
    r"(?:[\w#.+/-]+\s+){0,3}?(?:experience|experiencia)",
    re.I,
)
_REMOTE_WORDS = re.compile(r"\b(?:fully remote|100% remote|remote|remoto)\b|[()]", re.I)


def _phrase_pattern(phrase: str) -> str:
    return rf"(?<![a-z0-9]){re.escape(phrase.lower())}(?![a-z0-9#+])"


@lru_cache(maxsize=8)
def _compiled(synonyms_key: tuple[tuple[str, tuple[str, ...]], ...]) -> dict[str, re.Pattern[str]]:
    return {term: re.compile("|".join(_phrase_pattern(a) for a in aliases)) for term, aliases in synonyms_key}


def _patterns(cfg: Config) -> dict[str, re.Pattern[str]]:
    return _compiled(tuple((k, tuple(v)) for k, v in cfg.synonyms.items()))


def _contains_any(text: str, phrases: list[str]) -> str | None:
    low = text.lower()
    for phrase in phrases:
        if re.search(_phrase_pattern(phrase), low):
            return phrase
    return None


def find_terms(text: str, cfg: Config) -> set[str]:
    low = text.lower()
    return {term for term, pattern in _patterns(cfg).items() if pattern.search(low)}


def extract_terms(title: str, description: str, cfg: Config) -> dict[str, float]:
    """Canonical tech terms in a posting with their weight (title > required > nice-to-have)."""
    s = cfg.scoring
    weights: dict[str, float] = {term: s.title_term_weight for term in find_terms(title, cfg)}
    required: set[str] = set()
    nice: set[str] = set()
    in_nice = False
    for line in description.splitlines():
        header = _NICE_HEADER.search(line)
        if header:
            # Text before the marker keeps the current mode; text after it is nice-to-have.
            (nice if in_nice else required).update(find_terms(line[: header.start()], cfg))
            nice.update(find_terms(line[header.start():], cfg))
            # Only a heading-like line ("Nice to have:") opens a nice-to-have block for the next lines.
            in_nice = len(line) < 40 or line.rstrip().endswith(":")
            continue
        if len(line) < 40 and line.rstrip().endswith(":"):
            in_nice = False  # a new section heading ends the nice-to-have block
        (nice if in_nice else required).update(find_terms(line, cfg))
    for term in required:
        weights[term] = max(weights.get(term, 0), s.description_term_weight)
    for term in nice - required:
        weights[term] = max(weights.get(term, 0), s.nice_to_have_weight)
    return weights


def build_vocabulary(profile: dict, cfg: Config) -> dict[str, float]:
    """Profile strength per canonical term (0..1) from highlight tags and the skills section."""
    s = cfg.scoring
    evidence_weight = {"verified": 1.0, "partial": 0.5}
    counts: dict[str, float] = {}
    entries = [*profile.get("experience", []), *profile.get("projects", []), *profile.get("education", [])]
    for entry in entries:
        for highlight in entry.get("highlights", []):
            weight = evidence_weight.get(highlight.get("evidence"), 0.5)
            for tag in highlight.get("tags", []):
                counts[tag] = counts.get(tag, 0) + weight
    saturation = math.log2(1 + s.profile_saturation)
    vocab = {tag: min(1.0, math.log2(1 + n) / saturation) for tag, n in counts.items() if tag in cfg.synonyms}
    listed = [d for group in profile.get("skills", []) for d in group.get("details", [])]
    listed += [item for project in profile.get("projects", []) for item in project.get("stack", [])]
    for text in listed:
        for term in find_terms(text, cfg):
            vocab[term] = max(vocab.get(term, 0), s.skills_min_strength)
    return {term: round(value, 4) for term, value in vocab.items() if value > 0}


def zone_for(score: int, cfg: Config) -> str:
    zones = cfg.scoring.zones
    if score >= zones.apply:
        return "apply"
    if score >= zones.review:
        return "review"
    return "low"


def passes_filters(job: Job, cfg: Config) -> tuple[bool, str | None]:
    """Stage 1: hard rules. Returns (passes, reason when dropped)."""
    f = cfg.filters
    if not _contains_any(job.title, f.title_must_match_any):
        return False, "not a software role"
    excluded = _contains_any(job.title, f.exclude_title_keywords)
    if excluded:
        return False, f"title contains '{excluded}'"
    stack = _contains_any(job.title, f.exclude_title_stacks_without_core)
    if stack and not (find_terms(f"{job.title}\n{job.description}", cfg) & set(cfg.scoring.core_terms)):
        return False, f"{stack} role without the core stack"
    mode, relocation = _work_mode(job)
    if mode == "onsite" and not relocation:
        return False, "on-site without relocation"
    if mode == "hybrid" and job.country not in f.onsite_countries and not relocation:
        return False, "on-site outside the allowed countries"
    return True, None


def _work_mode(job: Job) -> tuple[str, bool]:
    """Work mode and relocation offer, derived from the posting text (see jobs.text)."""
    return (work_mode(job.title, job.location, job.description, job.remote),
            offers_relocation(f"{job.title}\n{job.description}"))


def _region_restricted(job: Job, cfg: Config) -> bool:
    if not job.remote or job.market == "peru":
        return False
    # Any stated location (city, country, region) that is not open to Peru/LatAm restricts the role.
    detail = _REMOTE_WORDS.sub(" ", job.location).strip(" ,-/")
    return bool(detail) and not _contains_any(job.location, cfg.scoring.eligible_regions)


def score_job(job: Job, vocab: dict[str, float], cfg: Config) -> Job:
    """Stage 2: deterministic 0-100 score with matched/missing keywords and short reasons."""
    s, adj = cfg.scoring, cfg.scoring.adjustments
    terms = extract_terms(job.title, job.description, cfg)
    total = sum(terms.values())
    matched = {t: w for t, w in terms.items() if t in vocab}
    missing = {t: w for t, w in terms.items() if t not in vocab}
    coverage = sum(w * (0.6 + 0.4 * vocab[t]) for t, w in matched.items()) / total if total else 0.0
    core = min(1.0, sum(weight for term, weight in s.core_terms.items() if term in terms))
    # Thin postings (few tech terms) cannot prove a fit: scale coverage down until enough evidence.
    evidence = min(1.0, 0.5 + 0.5 * total / s.min_evidence_weight) if s.min_evidence_weight else 1.0
    score = s.coverage_weight * coverage * evidence + s.core_weight * core

    positives: list[str] = []
    negatives: list[str] = []
    top = sorted(matched, key=lambda t: (-matched[t] * vocab[t], t))[:4]
    if top:
        strength = "fuerte" if coverage >= 0.75 else "parcial"
        positives.append(f"Coincidencia {strength} de stack: {', '.join(cfg.label(t) for t in top)}")
    else:
        negatives.append("Sin coincidencias con el stack del perfil")

    if job.remote and job.market == "abroad":
        if _region_restricted(job, cfg):
            score -= adj.region_restricted_penalty
            negatives.append(f"Remoto pero restringido: {job.location}")
        else:
            score += adj.remote_abroad_bonus
            positives.append("Puesto remoto abierto al extranjero")
    elif job.market == "peru":
        score += adj.peru_bonus
        positives.append("Puesto remoto en Perú" if job.remote else "Puesto en Perú")

    senior = _contains_any(job.title, s.seniority.too_senior_title)
    if senior:
        score -= adj.too_senior_penalty
        negatives.append(f"El título sugiere nivel {senior}")
    elif _contains_any(job.title, s.seniority.junior_title):
        score -= adj.junior_penalty
        negatives.append("Puesto junior, por debajo del nivel actual")
    years = [int(n) for n in _YEARS.findall(job.description) if 0 < int(n) <= 25]
    if years and max(years) > s.seniority.max_years_required:
        score -= adj.years_penalty
        negatives.append(f"Pide {max(years)}+ años de experiencia")
    excluded = _contains_any(f"{job.title}\n{job.description}\n{job.location}", s.exclusion_keywords)
    if excluded:
        score -= adj.exclusion_penalty
        negatives.append(f"Requisito: {excluded}")
    if evidence < 1:
        negatives.append("La oferta trae pocos detalles técnicos")
    if missing:
        top_missing = sorted(missing, key=lambda t: (-missing[t], t))[:3]
        negatives.append(f"Falta: {', '.join(cfg.label(t) for t in top_missing)}")

    final = max(0, min(100, round(score)))
    reasons = (positives[:2] + negatives)[:4]
    if len(reasons) < 2:
        reasons.append(f"Cobertura de palabras clave: {round(coverage * 100)}%")
    mode, relocation = _work_mode(job)
    return job.model_copy(update={
        "work_mode": mode,
        "relocation": relocation,
        "score": final,
        "zone": zone_for(final, cfg),
        "matched": sorted(matched, key=lambda t: (-matched[t], t)),
        "missing": sorted(missing, key=lambda t: (-missing[t], t)),
        "reasons": reasons,
    })
