"""Tests for cv/tailor.py: the deterministic helpers behind the `/tailor <job-id>` command."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pypdf
import pytest
from ruamel.yaml import YAML

import build
import tailor

CV_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = CV_DIR.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"
TAILOR = CV_DIR / "tailor.py"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def profile() -> dict:
    return tailor.load_profile()


@pytest.fixture(scope="module")
def cfg():
    return tailor.load_scoring_config()


@pytest.fixture()
def selection_en() -> dict:
    return load_fixture("selection_en.json")


@pytest.fixture()
def selection_es() -> dict:
    return load_fixture("selection_es.json")


def peru_job() -> dict:
    return {
        "id": "job-0000peru",
        "title": "Desarrollador .NET Full Stack",
        "company": "Empresa de prueba",
        "location": "Lima, Peru",
        "market": "peru",
        "description": "Buscamos desarrollador con C#, .NET, Angular y SQL Server.\nDeseable: Kubernetes.",
        "matched": ["csharp", "dotnet", "angular", "sql-server"],
        "missing": ["kubernetes"],
        "score": 80,
    }


# --- S5: language by market -------------------------------------------------------------------


def test_language_follows_market():
    assert tailor.language_for({"market": "peru"}) == "es"
    assert tailor.language_for({"market": "abroad"}) == "en"


# --- S2: never invent ---------------------------------------------------------------------------


def test_fixture_selections_are_valid(profile, cfg, selection_en, selection_es):
    assert tailor.validate_selection(selection_en, profile, "en", cfg) == []
    assert tailor.validate_selection(selection_es, profile, "es", cfg) == []


def test_unknown_id_is_rejected(profile, cfg, selection_en):
    selection_en["experience"]["komatsu-mitsui"].append({"ids": ["made-up-claim"], "text": "Led a team."})
    errors = tailor.validate_selection(selection_en, profile, "en", cfg)
    assert any("made-up-claim" in e and "not in the bank" in e for e in errors), errors


def test_id_from_another_entry_is_rejected(profile, cfg, selection_en):
    selection_en["experience"]["cloud-store"].append({"ids": ["komatsu-sql-optimization"]})
    errors = tailor.validate_selection(selection_en, profile, "en", cfg)
    assert any("komatsu-sql-optimization" in e and "cloud-store" in e for e in errors), errors


def test_rephrase_adding_a_number_is_rejected(profile, cfg, selection_en):
    selection_en["experience"]["cloud-store"][1] = {
        "ids": ["cloudstore-bsale-integration"],
        "text": "Integrated SQL Server with the Bsale API, reducing manual data-entry errors by 40%.",
    }
    errors = tailor.validate_selection(selection_en, profile, "en", cfg)
    assert any("40" in e for e in errors), errors


def test_rephrase_adding_a_technology_is_rejected(profile, cfg, selection_en):
    selection_en["experience"]["komatsu-mitsui"][0] = {
        "ids": ["komatsu-react-migration"],
        "text": "Migrated an activity-planning application from ASP.NET MVC to React on Kubernetes.",
    }
    errors = tailor.validate_selection(selection_en, profile, "en", cfg)
    assert any("kubernetes" in e for e in errors), errors


def test_summary_with_unbacked_technology_is_rejected(profile, cfg, selection_en):
    selection_en["summary"] += " Runs Kafka clusters."
    errors = tailor.validate_selection(selection_en, profile, "en", cfg)
    assert any("summary" in e and "kafka" in e for e in errors), errors


def test_excluded_question_mark_claims_are_rejected(profile, cfg, selection_en):
    selection_en["experience"]["maquinarias-glory"][0]["text"] = "Developed React quotation features ❓."
    errors = tailor.validate_selection(selection_en, profile, "en", cfg)
    assert any("❓" in e for e in errors), errors


def test_duplicate_id_is_rejected(profile, cfg, selection_en):
    selection_en["experience"]["komatsu-mitsui"].append({"ids": ["komatsu-sql-optimization"]})
    errors = tailor.validate_selection(selection_en, profile, "en", cfg)
    assert any("komatsu-sql-optimization" in e and "more than once" in e for e in errors), errors


def test_every_role_keeps_a_bullet(profile, cfg, selection_en):
    del selection_en["experience"]["maquinarias-glory"]
    errors = tailor.validate_selection(selection_en, profile, "en", cfg)
    assert any("maquinarias-glory" in e for e in errors), errors


def test_merged_bullet_needs_text(profile, cfg, selection_en):
    selection_en["experience"]["komatsu-mitsui"] = [{"ids": ["komatsu-react-migration", "komatsu-sql-optimization"]}]
    errors = tailor.validate_selection(selection_en, profile, "en", cfg)
    assert any("text" in e and "komatsu" in e for e in errors), errors


def test_spanish_needs_text_when_highlight_has_no_text_es(profile, cfg, selection_es):
    selection_es["experience"]["cloud-store"] = [{"ids": ["cloudstore-invoicing-app"]}]
    errors = tailor.validate_selection(selection_es, profile, "es", cfg)
    assert any("cloudstore-invoicing-app" in e and "text_es" in e for e in errors), errors


def test_skills_come_from_the_bank(profile, cfg, selection_en):
    selection_en["skills"][0]["details"].append("Kubernetes")
    errors = tailor.validate_selection(selection_en, profile, "en", cfg)
    assert any("Kubernetes" in e and "skills" in e for e in errors), errors


# --- S1: ranking by the job's keywords ----------------------------------------------------------


def test_context_ranks_bullets_by_job_keywords(profile, cfg):
    job = {
        "id": "job-0000aaaa", "title": "Search Engineer (Meilisearch)", "company": "Acme",
        "location": "Remote", "market": "abroad", "score": 70, "matched": ["meilisearch"], "missing": [],
        "description": "Build search with Meilisearch and .NET.",
    }
    context = tailor.build_context(job, profile, cfg)
    assert context["language"] == "en"
    bertoni = next(e for e in context["entries"] if e["id"] == "bertoni-solutions")
    assert "meilisearch" in bertoni["highlights"][0]["covers"]
    relevance = [h["relevance"] for h in bertoni["highlights"]]
    assert relevance == sorted(relevance, reverse=True)
    assert "meilisearch" in context["job"]["terms"]


def test_context_states_spanish_for_peru(profile, cfg):
    context = tailor.build_context(peru_job(), profile, cfg)
    assert context["language"] == "es"
    assert "peru" in context["language_reason"]


# --- S3 / S5: YAML generation -------------------------------------------------------------------


def test_yaml_keeps_base_design_and_uses_the_selection(profile, selection_en):
    base = tailor.load_base()
    doc = tailor.render_yaml(selection_en, profile, base, "en")
    assert doc["design"] == base["design"]
    assert doc["locale"] == base["locale"]
    assert list(doc["cv"]["sections"]) == list(base["cv"]["sections"])
    for key in ("name", "headline", "location", "phone", "email", "social_networks"):
        assert doc["cv"][key] == base["cv"][key]
    summary = doc["cv"]["sections"]["​"]
    assert summary == [f"*{selection_en['summary']}*"]
    experience = doc["cv"]["sections"]["PROFESSIONAL EXPERIENCE"]
    assert [e["company"] for e in experience] == [e["company"] for e in base["cv"]["sections"]["PROFESSIONAL EXPERIENCE"]]
    bertoni = experience[0]
    assert bertoni["highlights"][0] == selection_en["experience"]["bertoni-solutions"][0]["text"]
    bank_text = tailor.highlight_index(profile)["proquinorte-search-microservice"]["highlight"]["text"]
    assert bertoni["highlights"][2] == bank_text
    skills = doc["cv"]["sections"]["TECHNOLOGIES AND SKILLS"]
    assert skills[0] == {"label": "Backend", "details": "C#, .NET, ASP.NET Core, Entity Framework Core, REST APIs and integrations."}
    assert skills[-1] == {"label": "Languages", "details": "Spanish - Native · English - B2."}


def test_spanish_yaml_translates_headings_and_uses_text_es(profile, selection_es):
    doc = tailor.render_yaml(selection_es, profile, tailor.load_base(), "es")
    sections = list(doc["cv"]["sections"])
    assert sections == ["​", "EXPERIENCIA PROFESIONAL", "PROYECTO PERSONAL", "EDUCACIÓN", "TECNOLOGÍAS Y HABILIDADES"]
    assert doc["locale"]["language"] == "spanish"
    bertoni = doc["cv"]["sections"]["EXPERIENCIA PROFESIONAL"][0]
    text_es = tailor.highlight_index(profile)["nexo-b2b-platform"]["highlight"]["text_es"]
    assert text_es in bertoni["highlights"]
    education = doc["cv"]["sections"]["EDUCACIÓN"][0]
    assert education["highlights"] == [b["text"] for b in selection_es["education"]["unmsm"]]
    skills = doc["cv"]["sections"]["TECNOLOGÍAS Y HABILIDADES"]
    assert skills[-1] == {"label": "Idiomas", "details": "Español - Nativo · Inglés - B2."}


# --- CLI ----------------------------------------------------------------------------------------


def run_tailor(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TAILOR), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env={**build.utf8_env()},
    )


def write_json(path: Path, data) -> Path:
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def test_cli_build_rejects_unknown_id_without_rendering(tmp_path, selection_en):
    selection_en["experience"]["komatsu-mitsui"][0] = {"ids": ["made-up-claim"], "text": "Did things."}
    jobs = write_json(tmp_path / "jobs.json", {"jobs": [peru_job() | {"market": "abroad", "id": "job-0000aaaa"}]})
    selection = write_json(tmp_path / "selection.json", selection_en)
    out = tmp_path / "out"
    result = run_tailor("build", "job-0000aaaa", "--jobs", str(jobs), "--selection", str(selection),
                        "--tailored-dir", str(tmp_path / "tailored"), "--out", str(out))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "made-up-claim" in result.stderr
    assert not out.exists() or not list(out.glob("*.pdf"))


def test_cli_build_rejects_unknown_job(tmp_path):
    jobs = write_json(tmp_path / "jobs.json", {"jobs": []})
    result = run_tailor("build", "job-ffffffff", "--jobs", str(jobs))
    assert result.returncode == 1
    assert "job-ffffffff" in result.stderr


def test_cli_context_prints_json(tmp_path):
    jobs = write_json(tmp_path / "jobs.json", {"jobs": [peru_job()]})
    result = run_tailor("context", "job-0000peru", "--jobs", str(jobs))
    assert result.returncode == 0, result.stderr
    context = json.loads(result.stdout)
    assert context["language"] == "es"
    assert context["job"]["id"] == "job-0000peru"
    assert context["selection_path"].endswith("job-0000peru.selection.json")


# --- S3 / S4 / S6 / S7: end-to-end render -------------------------------------------------------


def highest_scoring_job() -> dict:
    jobs = json.loads((REPO_ROOT / "data" / "jobs.json").read_text(encoding="utf-8"))["jobs"]
    if not jobs:
        pytest.skip("data/jobs.json has no jobs")
    return max(jobs, key=lambda job: job["score"])


def render_end_to_end(tmp_path: Path, job_id: str, jobs_path: Path, selection: dict):
    selection_path = write_json(tmp_path / "selection.json", selection)
    tailored, out = tmp_path / "tailored", tmp_path / "out"
    result = run_tailor("build", job_id, "--jobs", str(jobs_path), "--selection", str(selection_path),
                        "--tailored-dir", str(tailored), "--out", str(out))
    assert result.returncode == 0, result.stdout + result.stderr
    pdf = out / f"{job_id}.pdf"
    source = YAML(typ="safe").load((tailored / f"{job_id}.yaml").read_text(encoding="utf-8"))
    return result, pdf, source, tailored, out


def assert_rendered_cv(result, pdf: Path, source: dict, tailored: Path, out: Path, job_id: str):
    pages = len(pypdf.PdfReader(pdf).pages)
    assert 1 <= pages <= 2
    assert sorted(p.name for p in out.glob(f"{job_id}_*.png")) == [f"{job_id}_{n}.png" for n in range(1, pages + 1)]
    assert build.ats_problems(pdf, source["cv"], source.get("locale")) == []
    meta = json.loads((tailored / f"{job_id}.meta.json").read_text(encoding="utf-8"))
    assert meta["id"] == job_id and meta["title"] and meta["company"]
    assert "Covered keywords:" in result.stdout
    assert "Missing keywords:" in result.stdout
    assert f"Pages: {pages}" in result.stdout
    assert f"{job_id}.pdf" in result.stdout


def test_end_to_end_highest_scoring_job_in_english(tmp_path, selection_en):
    job = highest_scoring_job()
    if job["market"] != "abroad":
        pytest.skip("the English end-to-end check needs an abroad job on top")
    result, pdf, source, tailored, out = render_end_to_end(tmp_path, job["id"], REPO_ROOT / "data" / "jobs.json", selection_en)
    assert_rendered_cv(result, pdf, source, tailored, out, job["id"])


def test_end_to_end_peru_job_in_spanish(tmp_path, selection_es):
    jobs = write_json(tmp_path / "jobs.json", {"jobs": [peru_job()]})
    result, pdf, source, tailored, out = render_end_to_end(tmp_path, "job-0000peru", jobs, copy.deepcopy(selection_es))
    assert_rendered_cv(result, pdf, source, tailored, out, "job-0000peru")
    text = build.normalize(" ".join(page.extract_text() for page in pypdf.PdfReader(pdf).pages))
    assert "EXPERIENCIA PROFESIONAL" in text
    assert "Presente" in text
