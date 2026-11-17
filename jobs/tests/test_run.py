"""End-to-end pipeline test with stubbed sources and JSON output shape."""

import json
from datetime import date

from jobs import run as run_module
from jobs.models import SourceSummary
from jobs.sources import himalayas, remoteok, remotive

from .conftest import load_fixture


def stub_sources(monkeypatch):
    monkeypatch.setattr(remotive, "fetch", lambda cfg, s, today, **k: (remotive.parse(load_fixture("remotive.json"), today, 4000), []))
    monkeypatch.setattr(remoteok, "fetch", lambda cfg, s, today, **k: (remoteok.parse(load_fixture("remoteok.json"), today, 4000), []))
    monkeypatch.setattr(himalayas, "fetch", lambda cfg, s, today, **k: (himalayas.parse(load_fixture("himalayas.json"), today, 4000), []))


def test_pipeline_writes_sorted_valid_output(cfg, profile, tmp_path, monkeypatch, today):
    stub_sources(monkeypatch)
    out = tmp_path / "jobs.json"
    result = run_module.run_pipeline(
        cfg, profile, ["remotive", "remoteok", "himalayas"], today=today, output=out, session=None,
    )
    data = json.loads(out.read_text(encoding="utf-8"))
    assert set(data) == {"generated_at", "sources", "jobs"}
    assert [s["name"] for s in data["sources"]] == ["remotive", "remoteok", "himalayas"]
    assert all(set(s) <= {"name", "count", "error"} for s in data["sources"])
    jobs = data["jobs"]
    scores = [j["score"] for j in jobs]
    assert scores == sorted(scores, reverse=True)
    assert len({j["id"] for j in jobs}) == len(jobs)
    titles = [j["title"] for j in jobs]
    # Marketing, PHP and Java-only postings are filtered or fall below the keep threshold.
    assert "Growth Marketer" not in titles and "PHP Developer" not in titles
    assert "Java Backend Developer" not in titles
    assert titles[0] in {"Senior .NET Engineer (C#, Azure, Angular)", "Full Stack .NET Developer"}
    expected_keys = {
        "id", "title", "company", "location", "remote", "work_mode", "relocation", "country", "salary", "url", "source", "attribution",
        "posted_at", "expires_at", "first_seen", "last_seen", "description", "score", "zone", "matched",
        "missing", "reasons", "market",
    }
    assert set(jobs[0]) == expected_keys
    assert jobs[0]["first_seen"] == "2026-11-16"
    assert result.jobs == len(jobs)


def test_rerun_preserves_first_seen(cfg, profile, tmp_path, monkeypatch):
    stub_sources(monkeypatch)
    out = tmp_path / "jobs.json"
    run_module.run_pipeline(cfg, profile, ["remotive"], today=date(2026, 11, 16), output=out, session=None)
    run_module.run_pipeline(cfg, profile, ["remotive"], today=date(2026, 11, 18), output=out, session=None)
    job = json.loads(out.read_text(encoding="utf-8"))["jobs"][0]
    assert job["first_seen"] == "2026-11-16"
    assert job["last_seen"] == "2026-11-18"


def test_dry_run_does_not_write(cfg, profile, tmp_path, monkeypatch, today):
    stub_sources(monkeypatch)
    out = tmp_path / "jobs.json"
    run_module.run_pipeline(cfg, profile, ["remotive"], today=today, output=out, session=None, dry_run=True)
    assert not out.exists()


def test_limit_caps_jobs_per_source(cfg, profile, tmp_path, monkeypatch, today):
    stub_sources(monkeypatch)
    result = run_module.run_pipeline(
        cfg, profile, ["remotive"], today=today, output=tmp_path / "j.json", session=None, limit=1,
    )
    assert result.summaries == [SourceSummary(name="remotive", count=1)]


def test_cli_parses_sources(monkeypatch):
    args = run_module.parse_args(["--dry-run", "--sources", "remotive,himalayas", "--limit", "5"])
    assert args.dry_run is True and args.sources == ["remotive", "himalayas"] and args.limit == 5


def test_rescore_only_rescores_existing_file_without_fetching(cfg, profile, tmp_path, monkeypatch, today):
    stub_sources(monkeypatch)
    out = tmp_path / "jobs.json"
    run_module.run_pipeline(cfg, profile, ["remotive"], today=today, output=out, session=None)
    before = json.loads(out.read_text(encoding="utf-8"))
    for job in before["jobs"]:
        job["reasons"] = ["stale"]
    out.write_text(json.dumps(before), encoding="utf-8")

    def no_fetch(*args, **kwargs):
        raise AssertionError("rescore must not fetch")

    monkeypatch.setattr(remotive, "fetch", no_fetch)
    result = run_module.rescore_file(cfg, profile, out)
    after = json.loads(out.read_text(encoding="utf-8"))
    assert after["generated_at"] == before["generated_at"]
    assert after["sources"] == before["sources"]
    assert [j["id"] for j in after["jobs"]] == [j["id"] for j in before["jobs"]]
    assert all(j["reasons"] != ["stale"] for j in after["jobs"])
    keep = ("first_seen", "last_seen", "source", "url", "score")
    assert [{k: j[k] for k in keep} for j in after["jobs"]] == [{k: j[k] for k in keep} for j in before["jobs"]]
    assert result.jobs == len(after["jobs"])


def test_cli_parses_rescore_only():
    assert run_module.parse_args(["--rescore-only"]).rescore_only is True
    assert run_module.parse_args([]).rescore_only is False
