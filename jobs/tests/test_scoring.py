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
    assert scored.reasons[0].startswith("Coincidencia fuerte de stack: ")
    assert any(r.startswith("Falta: ") for r in scored.reasons)


def test_reasons_are_spanish(cfg, profile):
    vocab = build_vocabulary(profile, cfg)
    assert "Puesto remoto abierto al extranjero" in score_job(DOTNET_JOB, vocab, cfg).reasons
    assert "Sin coincidencias con el stack del perfil" in score_job(job("Backend Developer", "Java and Kafka."), vocab, cfg).reasons
    years = score_job(DOTNET_JOB.model_copy(update={"description": DOTNET_JOB.description + " 10+ years of experience."}), vocab, cfg)
    assert "Pide 10+ años de experiencia" in years.reasons
    peru = score_job(DOTNET_JOB.model_copy(update={"market": "peru", "location": "Lima"}), vocab, cfg)
    assert "Puesto remoto en Perú" in peru.reasons


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
    assert any(r.startswith("Remoto pero restringido: ") for r in restricted.reasons)
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
        assert any(r.startswith("Remoto pero restringido: ") for r in scored.reasons), location
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
    assert "La oferta trae pocos detalles técnicos" in thin.reasons


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
    # On-site outside Peru is dropped.
    assert not passes_filters(job(".NET Developer", "C#", remote=False, location="Dallas, TX", country="US"), cfg)[0]


def test_onsite_is_dropped_unless_it_offers_relocation(cfg):
    lima = dict(remote=False, location="Lima", country="PE", market="peru")
    assert passes_filters(job(".NET Developer", "C#", **lima), cfg) == (False, "on-site without relocation")
    assert passes_filters(job(".NET Developer", "C#. Relocation package to Madrid.", remote=False,
                              location="Madrid, Spain", country="ES"), cfg)[0]
    assert not passes_filters(job(".NET Developer", "C#. No relocation assistance.", **lima), cfg)[0]


def test_hybrid_is_kept_in_peru_and_dropped_abroad_without_relocation(cfg):
    assert passes_filters(job(".NET Developer", "C#. Modalidad híbrida, 2 días en oficina.", remote=False,
                              location="Lima", country="PE", market="peru"), cfg)[0]
    assert not passes_filters(job(".NET Developer (Hybrid)", "C#", remote=False, location="Austin, TX",
                                  country="US"), cfg)[0]


def test_work_mode_and_relocation_are_recorded(cfg):
    vocab = build_vocabulary(json.loads((REPO_ROOT / "data" / "profile.json").read_text(encoding="utf-8")), cfg)
    assert score_job(DOTNET_JOB, vocab, cfg).work_mode == "remote"
    hybrid = score_job(job(".NET Dev", "C#. Hybrid: 3 days in office.", remote=False, location="Lima",
                           country="PE", market="peru"), vocab, cfg)
    assert (hybrid.work_mode, hybrid.relocation) == ("hybrid", False)
    reloc = score_job(job(".NET Dev", "C#. We offer visa sponsorship and relocation support.", remote=False,
                          location="Berlin, Germany", country="DE"), vocab, cfg)
    assert (reloc.work_mode, reloc.relocation) == ("onsite", True)
    # "hybrid" in the title/location wins over a remote flag set by a loose text match.
    assert score_job(job(".NET Dev", "C#", remote=True, location="Lima (Hybrid)", country="PE", market="peru"),
                     vocab, cfg).work_mode == "hybrid"
