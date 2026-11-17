"""Source parsing tests: recorded/synthetic payloads, no network."""

from datetime import date

import pytest

from jobs.models import make_job_id
from jobs.run import collect
from jobs.sources import himalayas, jobspy_source, remoteok, remotive

from .conftest import load_fixture


def test_remotive_parse_normalizes_fields(today):
    jobs = remotive.parse(load_fixture("remotive.json"), today, max_chars=4000)
    assert len(jobs) == 3
    job = jobs[0]
    assert job.source == "remotive"
    assert job.title == "Senior .NET Engineer (C#, Azure, Angular)"
    assert job.company == "Acme Cloud Inc."
    assert job.remote is True
    assert job.location == "Remote (Latin America)"
    assert job.posted_at == date(2026, 11, 14)
    assert job.first_seen == today and job.last_seen == today
    assert "<" not in job.description and "Azure Functions" in job.description
    assert job.salary is not None
    assert (job.salary.min, job.salary.max, job.salary.currency, job.salary.period) == (60000, 80000, "USD", "yearly")
    assert job.attribution is not None and job.attribution.name == "Remotive"
    assert job.attribution.url == job.url
    assert job.id == make_job_id(job.url)


def test_remotive_empty_salary_is_null(today):
    jobs = remotive.parse(load_fixture("remotive.json"), today, max_chars=4000)
    assert jobs[1].salary is None


def test_remoteok_skips_legal_item_and_maps_salary(today):
    jobs = remoteok.parse(load_fixture("remoteok.json"), today, max_chars=4000)
    assert [j.title for j in jobs] == ["Full Stack .NET Developer", "PHP Developer"]
    first, second = jobs
    assert first.source == "remoteok" and first.remote is True
    assert first.salary is not None and first.salary.min == 50000 and first.salary.currency == "USD"
    assert second.salary is None  # zeros mean "not provided"
    assert second.location == "Remote"
    assert first.attribution is not None and first.attribution.name == "Remote OK"
    assert first.posted_at == date(2026, 11, 14)


def test_himalayas_drops_expired_and_keeps_application_link(today):
    jobs = himalayas.parse(load_fixture("himalayas.json"), today, max_chars=4000)
    assert len(jobs) == 1
    job = jobs[0]
    # Terms: the Apply link must be the applicationLink, unchanged.
    assert job.url == "https://himalayas.app/companies/zeta-software/jobs/software-engineer-net?utm_source=api"
    assert job.attribution is not None
    assert job.attribution.url == "https://himalayas.app/companies/zeta-software/jobs/software-engineer-net"
    assert job.location == "Remote (Peru, Colombia, Mexico)"
    assert job.salary is not None and job.salary.period == "yearly"
    assert job.expires_at is not None
    # The id ignores tracking parameters, so it equals the id of the guid.
    assert job.id == make_job_id(job.attribution.url)


def test_himalayas_long_region_list_keeps_peru_visible(today):
    payload = load_fixture("himalayas.json")
    item = dict(payload["jobs"][0])
    item["locationRestrictions"] = ["Argentina", "Brazil", "Chile", "Colombia", "Cuba", "Ecuador", "Mexico", "Peru"]
    jobs = himalayas.parse({"jobs": [item]}, today, max_chars=4000)
    assert "Peru" in jobs[0].location


def test_jobspy_rows_normalize_country_remote_and_ids(cfg, today):
    search = cfg.sources.jobspy.searches[0]  # peru
    rows = load_fixture("jobspy_rows.json")
    jobs = jobspy_source.rows_to_jobs(rows, search, today, max_chars=4000)
    by_source = {j.title: j for j in jobs}
    lima = by_source["Desarrollador .NET Semi Senior"]
    assert lima.source == "linkedin" and lima.country == "PE" and lima.market == "peru"
    assert lima.remote is False and lima.attribution is None
    # Tracking query parameters are not part of the id.
    assert lima.id == make_job_id("https://www.linkedin.com/jobs/view/3001")
    remote_us = by_source["Remote C# Developer"]
    assert remote_us.country == "US" and remote_us.market == "abroad" and remote_us.remote is True
    assert remote_us.salary is not None and remote_us.salary.period == "yearly"
    # Indeed keeps its `jk` parameter, which identifies the posting.
    assert remote_us.id == make_job_id("https://www.indeed.com/viewjob?jk=4001")
    assert remote_us.id != by_source[".NET Developer"].id


def test_jobspy_fetch_reports_per_site_errors(cfg, today):
    import pandas as pd

    rows = load_fixture("jobspy_rows.json")

    def fake_scrape(**kwargs):
        df = pd.DataFrame([r for r in rows if r["site"] in kwargs["site_name"]])
        df.attrs = {"errors": {"indeed": "blocked (403)"} if "indeed" in kwargs["site_name"] else {}}
        return df

    jobs, summaries = jobspy_source.fetch(cfg, None, today, scrape=fake_scrape, terms=["C#"])
    names = {s.name: s for s in summaries}
    assert names["indeed"].error and "403" in names["indeed"].error
    assert names["linkedin"].count >= 1 and names["linkedin"].error is None
    assert all(j.source in {"linkedin", "indeed", "google"} for j in jobs)


def test_collect_isolates_failing_source(cfg, today, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("network down")

    def ok(cfg_, session, today_, **kwargs):
        return remotive.parse(load_fixture("remotive.json"), today_, max_chars=4000), []

    monkeypatch.setattr(remoteok, "fetch", boom)
    monkeypatch.setattr(remotive, "fetch", ok)
    jobs, summaries = collect(cfg, ["remoteok", "remotive"], today, session=None)
    by_name = {s.name: s for s in summaries}
    assert by_name["remoteok"].error == "RuntimeError: network down"
    assert by_name["remoteok"].count == 0
    assert by_name["remotive"].count == 3 and by_name["remotive"].error is None
    assert len(jobs) == 3


def test_unknown_source_is_rejected(cfg, today):
    with pytest.raises(ValueError):
        collect(cfg, ["nope"], today, session=None)
