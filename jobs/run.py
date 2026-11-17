"""Job search pipeline: fetch -> normalize -> dedupe -> filter -> score -> data/jobs.json.

Usage (from the repo root):
    python -m jobs.run [--dry-run] [--sources jobspy,remotive,remoteok,himalayas] [--limit N]
    python -m jobs.run --rescore-only [--dry-run]   # offline: re-score the existing file, no fetch
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .config import REPO_ROOT, Config, load_config
from .dedupe import merge, prune
from .models import Job, JobsFile, SourceSummary
from .scoring import build_vocabulary, passes_filters, score_job
from .sources import himalayas, jobspy_source, remoteok, remotive

log = logging.getLogger("jobs")
SOURCES = {"jobspy": jobspy_source, "remotive": remotive, "remoteok": remoteok, "himalayas": himalayas}


@dataclass
class RunResult:
    summaries: list[SourceSummary]
    jobs: int
    zones: dict[str, int] = field(default_factory=dict)
    top: list[Job] = field(default_factory=list)
    filtered: int = 0


def enabled_sources(cfg: Config) -> list[str]:
    return [name for name in SOURCES if getattr(cfg.sources, name).enabled]


def collect(cfg: Config, names: list[str], today: date, session: Any,
            limit: int | None = None) -> tuple[list[Job], list[SourceSummary]]:
    """Run each source independently: an exception is recorded in its summary and the run continues."""
    unknown = [n for n in names if n not in SOURCES]
    if unknown:
        raise ValueError(f"Unknown source(s): {', '.join(unknown)}. Known: {', '.join(SOURCES)}")
    jobs: list[Job] = []
    summaries: list[SourceSummary] = []
    for name in names:
        try:
            found, subs = SOURCES[name].fetch(cfg, session, today)
        except Exception as error:  # noqa: BLE001 - isolate every source
            message = f"{type(error).__name__}: {error}"[:300]
            log.warning("source %s failed: %s", name, message)
            summaries.append(SourceSummary(name=name, count=0, error=message))
            continue
        if limit is not None:
            per_source: Counter[str] = Counter()
            capped = []
            for job in found:
                if per_source[job.source] < limit:
                    per_source[job.source] += 1
                    capped.append(job)
            found = capped
            subs = [s.model_copy(update={"count": min(s.count, limit)}) for s in subs]
        jobs.extend(found)
        summaries.extend(subs or [SourceSummary(name=name, count=len(found))])
        log.info("source %s: %d postings", name, len(found))
    return jobs, summaries


def load_previous(path: Path) -> list[Job]:
    if not path.is_file():
        return []
    try:
        return JobsFile.model_validate_json(path.read_text(encoding="utf-8")).jobs
    except (ValidationError, ValueError) as error:
        log.warning("ignoring unreadable %s: %s", path, str(error)[:200])
        return []


def score_pool(pool: list[Job], cfg: Config, profile: dict) -> list[Job]:
    """Filter, score, apply the keep threshold and sort: the step shared by a run and a re-score."""
    vocab = build_vocabulary(profile, cfg)
    scored = [score_job(job, vocab, cfg) for job in pool if passes_filters(job, cfg)[0]]
    kept = [job for job in scored if job.score >= cfg.scoring.min_score_to_keep]
    kept.sort(key=lambda j: (-j.score, -(j.posted_at or j.first_seen).toordinal(), j.title.lower(), j.id))
    return kept


def write_document(output: Path, document: dict[str, Any], dry_run: bool) -> None:
    JobsFile.model_validate(document)  # never write a file the site cannot read
    if not dry_run:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_pipeline(cfg: Config, profile: dict, names: list[str], *, today: date, output: Path, session: Any,
                 dry_run: bool = False, limit: int | None = None) -> RunResult:
    fresh, summaries = collect(cfg, names, today, session, limit)
    pool = prune(merge(load_previous(output), fresh, cfg.source_priority), today, cfg.output.prune_after_days)
    kept = score_pool(pool, cfg, profile)
    document = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "sources": [s.dump() for s in summaries],
        "jobs": [job.model_dump(mode="json") for job in kept],
    }
    write_document(output, document, dry_run)
    return RunResult(
        summaries=summaries,
        jobs=len(kept),
        zones=dict(Counter(job.zone for job in kept)),
        top=kept[:5],
        filtered=len(pool) - len(kept),
    )


def rescore_file(cfg: Config, profile: dict, output: Path, dry_run: bool = False) -> RunResult:
    """Offline: re-score the postings already in `output` with the current scorer, profile and config.

    Nothing is fetched. `generated_at`, `sources` and every posting's identity, dates and source fields
    are kept; only score, zone, matched, missing and reasons are recomputed (filters and the keep
    threshold apply as in a normal run).
    """
    raw = json.loads(output.read_text(encoding="utf-8"))
    current = JobsFile.model_validate(raw)
    kept = score_pool(current.jobs, cfg, profile)
    document = {**raw, "jobs": [job.model_dump(mode="json") for job in kept]}
    write_document(output, document, dry_run)
    return RunResult(
        summaries=current.sources,
        jobs=len(kept),
        zones=dict(Counter(job.zone for job in kept)),
        top=kept[:5],
        filtered=len(current.jobs) - len(kept),
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m jobs.run", description="Fetch, score and publish job postings.")
    parser.add_argument("--dry-run", action="store_true", help="run everything but do not write data/jobs.json")
    parser.add_argument("--sources", type=lambda s: [x.strip() for x in s.split(",") if x.strip()],
                        help=f"comma-separated subset of: {', '.join(SOURCES)} (default: enabled in config)")
    parser.add_argument("--limit", type=int, help="keep at most N postings per source (for quick checks)")
    parser.add_argument("--rescore-only", action="store_true",
                        help="offline: re-score the existing output file without fetching any source")
    parser.add_argument("--config", type=Path, help="alternative config file")
    parser.add_argument("--output", type=Path, help="alternative output file (default from config)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")  # Windows cp1252 consoles
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = parse_args(argv)
    cfg = load_config(args.config) if args.config else load_config()
    profile = json.loads((REPO_ROOT / "data" / "profile.json").read_text(encoding="utf-8"))
    output = args.output or REPO_ROOT / cfg.output.path

    if args.rescore_only:
        if not output.is_file():
            print(f"Nothing to re-score: {output} does not exist", file=sys.stderr)
            return 2
        result = rescore_file(cfg, profile, output, dry_run=args.dry_run)
    else:
        import requests

        with requests.Session() as session:
            try:
                result = run_pipeline(cfg, profile, args.sources or enabled_sources(cfg), today=date.today(),
                                      output=output, session=session, dry_run=args.dry_run, limit=args.limit)
            except ValueError as error:
                print(error, file=sys.stderr)
                return 2

    print("\nSources:")
    for s in result.summaries:
        print(f"  {s.name:<10} {s.count:>4}" + (f"  ERROR {s.error}" if s.error else ""))
    print(f"Jobs kept: {result.jobs} (dropped by filters/threshold: {result.filtered})")
    print("Zones: " + ", ".join(f"{z}={result.zones.get(z, 0)}" for z in ("apply", "review", "low")))
    for job in result.top:
        print(f"  {job.score:>3}  {job.title} - {job.company} [{job.source}]")
    print("(dry run, nothing written)" if args.dry_run else f"Wrote {output}")
    # Fail the run only when every source failed, so CI surfaces a total outage.
    return 1 if result.summaries and all(s.error and not s.count for s in result.summaries) else 0


if __name__ == "__main__":
    sys.exit(main())
