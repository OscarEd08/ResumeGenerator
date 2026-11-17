"""Dedupe, merge and prune tests."""

from datetime import date, timedelta

from jobs.dedupe import merge, prune
from jobs.models import Job, canonical_url, make_job_id


def make(url: str, title: str = ".NET Developer", company: str = "Acme", source: str = "remotive",
         seen: date = date(2026, 11, 16), description: str = "C# .NET") -> Job:
    return Job(
        id=make_job_id(url), title=title, company=company, location="Remote", remote=True,
        country=None, salary=None, url=url, source=source, attribution=None, posted_at=None,
        first_seen=seen, last_seen=seen, description=description, market="abroad",
    )


def test_id_is_stable_and_short():
    a = make_job_id("https://Example.com/jobs/1/?utm_source=x#top")
    b = make_job_id("https://example.com/jobs/1")
    assert a == b
    assert a.startswith("job-") and len(a) == 12
    assert make_job_id("https://example.com/jobs/2") != a


def test_canonical_url_keeps_identifying_query_params():
    assert canonical_url("https://www.indeed.com/viewjob?utm_campaign=a&jk=9") == "https://www.indeed.com/viewjob?jk=9"
    assert canonical_url("https://www.linkedin.com/jobs/view/1/?refId=a&trackingId=b") == "https://www.linkedin.com/jobs/view/1"


def test_merge_same_url_keeps_first_seen_and_updates_last_seen():
    old = make("https://x.com/j/1", seen=date(2026, 11, 1))
    new = make("https://x.com/j/1", seen=date(2026, 11, 16))
    merged = merge([old], [new], priority=["remotive"])
    assert len(merged) == 1
    assert merged[0].first_seen == date(2026, 11, 1)
    assert merged[0].last_seen == date(2026, 11, 16)


def test_merge_same_company_and_title_across_sources_keeps_previous_id():
    old = make("https://remotive.com/j/1", title="Senior .NET Engineer", company="Acme Inc.",
               seen=date(2026, 11, 10))
    new = make("https://www.linkedin.com/jobs/view/77", title="Senior .NET Engineer (Remote)",
               company="ACME", source="linkedin", description="much longer description " * 10)
    merged = merge([old], [new], priority=["remotive", "linkedin"])
    assert len(merged) == 1
    assert merged[0].id == old.id
    assert merged[0].first_seen == date(2026, 11, 10)
    assert merged[0].last_seen == date(2026, 11, 16)
    # The richer description wins.
    assert merged[0].description.startswith("much longer")


def test_merge_within_run_prefers_source_priority_on_ties():
    a = make("https://www.linkedin.com/jobs/view/5", source="linkedin")
    b = make("https://himalayas.app/j/5", source="himalayas")
    merged = merge([], [a, b], priority=["himalayas", "linkedin"])
    assert len(merged) == 1 and merged[0].source == "himalayas"


def test_merge_same_source_tie_takes_fresh_fields():
    old = make("https://x.com/j/9", seen=date(2026, 11, 1)).model_copy(update={"location": "Remote (Brazil, …)"})
    new = make("https://x.com/j/9").model_copy(update={"location": "Remote (Peru, Brazil)"})
    merged = merge([old], [new], priority=["remotive"])
    assert merged[0].location == "Remote (Peru, Brazil)"
    assert merged[0].id == old.id and merged[0].first_seen == date(2026, 11, 1)


def test_previous_jobs_not_seen_are_kept_until_pruned():
    old = make("https://x.com/j/old", title="Old role", seen=date(2026, 11, 1))
    new = make("https://x.com/j/new", title="New role")
    merged = merge([old], [new], priority=[])
    assert {j.title for j in merged} == {"Old role", "New role"}
    assert next(j for j in merged if j.title == "Old role").last_seen == date(2026, 11, 1)


def test_prune_drops_stale_and_expired_jobs():
    today = date(2026, 11, 16)
    fresh = make("https://x.com/a", title="A", seen=today - timedelta(days=30))
    stale = make("https://x.com/b", title="B", seen=today - timedelta(days=31))
    expired = make("https://x.com/c", title="C").model_copy(update={"expires_at": today - timedelta(days=1)})
    kept = prune([fresh, stale, expired], today, days=30)
    assert [j.title for j in kept] == ["A"]
