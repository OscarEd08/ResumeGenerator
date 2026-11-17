"""Filter and scoring tests (deterministic, explainable)."""

import json
from datetime import date
from pathlib import Path

from jobs.models import Job, make_job_id
from jobs.scoring import build_vocabulary, extract_terms, passes_filters, score_job, zone_for

REPO_ROOT = Path(__file__).resolve().parents[2]


def job(title: str, description: str, *, remote: bool = True, location: str = "Remote (Worldwide)",
        country: str | None = None, market: str = "abroad") -> Job:
    url = f"https://example.com/{abs(hash(title + description))}"
    return Job(
        id=make_job_id(url), title=title, company="Acme", location=location, remote=remote,
        country=country, salary=None, url=url, source="remotive", attribution=None, posted_at=None,
        first_seen=date(2026, 11, 16), last_seen=date(2026, 11, 16), description=description, market=market,
    )


DOTNET_JOB = job(
    "Senior .NET Engineer (C#, Azure)",
    "We use C#, .NET 8, ASP.NET Core Web API, Azure Functions, SQL Server, Angular and TypeScript. "
    "CI/CD with Azure DevOps. Nice to have: Kubernetes",
)
JAVA_JOB = job("Backend Developer", "Java 17, Spring Boot, Kafka, AWS and Kubernetes. PostgreSQL.")


def test_synonyms_normalize_to_canonical_terms(cfg):
    terms = extract_terms("Dotnet dev", "Experience with csharp, .NET Core, MSSQL and EF Core.", cfg)
    assert {"dotnet", "csharp", "sql-server", "entity-framework"} <= set(terms)


def test_angularjs_is_not_angular(cfg):
    terms = extract_terms("Frontend", "Legacy AngularJS app", cfg)
    assert "angularjs" in terms and "angular" not in terms


def test_javascript_does_not_match_java(cfg):
    terms = extract_terms("Dev", "JavaScript and TypeScript", cfg)
    assert "java" not in terms and "javascript" in terms


def test_title_terms_weigh_more_and_nice_to_have_less(cfg):
    terms = extract_terms(".NET Developer", "Requirements:\nC#\nNice to have:\nKubernetes", cfg)
    assert terms["dotnet"] > terms["csharp"] > terms["kubernetes"]


def test_vocabulary_from_profile_weights_frequent_tags_higher(cfg, profile):
    vocab = build_vocabulary(profile, cfg)
    assert vocab["dotnet"] > vocab["ci-cd"]
    # Skills-section terms are present even without highlight tags.
    assert vocab["postgresql"] >= cfg.scoring.skills_min_strength
    assert vocab["entity-framework"] >= cfg.scoring.skills_min_strength
    assert "java" not in vocab
    assert all(0 < v <= 1 for v in vocab.values())


def test_vocabulary_from_real_profile_has_core_stack(cfg):
    profile = json.loads((REPO_ROOT / "data" / "profile.json").read_text(encoding="utf-8"))
    vocab = build_vocabulary(profile, cfg)
    for term in ("dotnet", "csharp", "azure", "angular", "sql-server"):
        assert term in vocab


def test_dotnet_azure_angular_job_scores_high(cfg, profile):
    scored = score_job(DOTNET_JOB, build_vocabulary(profile, cfg), cfg)
    assert scored.score >= cfg.scoring.zones.apply
    assert scored.zone == "apply"
    assert {"dotnet", "csharp", "azure", "angular"} <= set(scored.matched)
    assert "kubernetes" in scored.missing
    assert 2 <= len(scored.reasons) <= 4
    assert any(".NET" in r for r in scored.reasons)


def test_java_only_job_scores_low(cfg, profile):
    scored = score_job(JAVA_JOB, build_vocabulary(profile, cfg), cfg)
    assert scored.score < 40
    assert scored.zone == "low"
    assert "java" in scored.missing


def test_region_restriction_and_seniority_penalties(cfg, profile):
    vocab = build_vocabulary(profile, cfg)
    base = score_job(DOTNET_JOB, vocab, cfg).score
    restricted = score_job(DOTNET_JOB.model_copy(update={"location": "Remote (USA only)"}), vocab, cfg)
    assert restricted.score <= base - cfg.scoring.adjustments.region_restricted_penalty + 1
    assert any("restricted" in r.lower() for r in restricted.reasons)
    principal = score_job(DOTNET_JOB.model_copy(update={"title": "Principal .NET Engineer (C#, Azure)"}), vocab, cfg)
    assert principal.score < base
    years = score_job(DOTNET_JOB.model_copy(update={"description": DOTNET_JOB.description + " 10+ years of experience."}), vocab, cfg)
    assert years.score < base


def test_remote_limited_to_other_countries_is_restricted(cfg, profile):
    vocab = build_vocabulary(profile, cfg)
    base = score_job(DOTNET_JOB, vocab, cfg).score
    for location in ("Remote (Brazil)", "Remote (Ireland)", "Austin, TX, US"):
        scored = score_job(DOTNET_JOB.model_copy(update={"location": location}), vocab, cfg)
        assert scored.score < base, location
        assert any("restricted" in r.lower() for r in scored.reasons), location
    for location in ("Remote", "Remote (Worldwide)", "Remote (Latin America)", "Remote (Peru, Colombia, Mexico)",
                     "Remote (USA, Canada, USA timezones)"):
        scored = score_job(DOTNET_JOB.model_copy(update={"location": location}), vocab, cfg)
        assert scored.score == base, location


def test_years_penalty_needs_experience_context(cfg, profile):
    vocab = build_vocabulary(profile, cfg)
    base = score_job(DOTNET_JOB, vocab, cfg).score
    for noise in (" Support 24 x 7.", " Over 20 years in business.", " Founded 15 years ago, we value experience."):
        unchanged = score_job(DOTNET_JOB.model_copy(update={"description": DOTNET_JOB.description + noise}), vocab, cfg)
        assert unchanged.score == base, noise
    spanish = score_job(DOTNET_JOB.model_copy(update={"description": DOTNET_JOB.description + " 8 años de experiencia."}), vocab, cfg)
    assert spanish.score < base


def test_job_text_fields_drop_invisible_characters():
    j = job("\ufeffSenior  .NET\u200b Developer", "C#")
    assert j.title == "Senior .NET Developer"


def test_thin_posting_scores_below_detailed_one(cfg, profile):
    vocab = build_vocabulary(profile, cfg)
    thin = score_job(job(".NET Developer", ""), vocab, cfg)
    assert thin.score < score_job(DOTNET_JOB, vocab, cfg).score
    assert thin.zone != "apply"
    assert "Few technical details in the posting" in thin.reasons


def test_score_is_clamped_and_zone_consistent(cfg, profile):
    vocab = build_vocabulary(profile, cfg)
    for j in (DOTNET_JOB, JAVA_JOB, job("Developer", "")):
        s = score_job(j, vocab, cfg)
        assert 0 <= s.score <= 100
        assert s.zone == zone_for(s.score, cfg)


def test_zone_thresholds(cfg):
    assert zone_for(85, cfg) == "apply"
    assert zone_for(84, cfg) == "review"
    assert zone_for(70, cfg) == "review"
    assert zone_for(69, cfg) == "low"


def test_filters(cfg):
    assert passes_filters(DOTNET_JOB, cfg)[0]
    assert not passes_filters(job("Growth Marketer", "Campaigns"), cfg)[0]
    assert not passes_filters(job(".NET Intern", "C#"), cfg)[0]
    # Java title without any core term is dropped; with a core term it stays.
    assert not passes_filters(job("Java Developer", "Spring Boot"), cfg)[0]
    assert passes_filters(job("Java / C# Developer", "C# and Java"), cfg)[0]
    # On-site outside Peru is dropped; on-site in Peru stays.
    assert not passes_filters(job(".NET Developer", "C#", remote=False, location="Dallas, TX", country="US"), cfg)[0]
    assert passes_filters(job(".NET Developer", "C#", remote=False, location="Lima", country="PE", market="peru"), cfg)[0]
