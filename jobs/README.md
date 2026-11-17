# Job search pipeline

Fetches job postings, normalizes and deduplicates them, filters and scores each one against
`data/profile.json`, and writes `data/jobs.json` for the site. Runs daily in GitHub Actions
(`.github/workflows/jobs.yml`) and locally. No paid service and no LLM is involved.

## Setup (from the repo root)

    py -3.13 -m venv .venv-jobs
    .venv-jobs/Scripts/python -m pip install -r jobs/requirements.txt   # Windows (.venv-jobs/bin/python elsewhere)

`python-jobspy` 1.4.1 installs on Python 3.13 (numpy 2.x); CI uses the same version.

## Run

    .venv-jobs/Scripts/python -m jobs.run                     # all enabled sources, writes data/jobs.json
    .venv-jobs/Scripts/python -m jobs.run --dry-run           # same, writes nothing
    .venv-jobs/Scripts/python -m jobs.run --sources remotive,himalayas --limit 10

- `--sources`: comma-separated subset of `jobspy, remotive, remoteok, himalayas`.
- `--limit N`: keep at most N postings per source (quick checks).
- `--config`, `--output`: alternative config or output file.

The run prints per-source counts and errors, the zone distribution and the top 5 postings. Output
is forced to UTF-8 so Windows consoles do not crash. The exit code is 1 only when every source failed.

## Test (offline, recorded fixtures)

    .venv-jobs/Scripts/python -m pytest jobs/tests -q
    npm run validate:jobs     # zod schema check of data/jobs.json (also in the deploy workflow)

## Config knobs (`jobs/config.yaml`)

| Key | Effect |
|---|---|
| `search_terms` | Queries for JobSpy, Remotive and Himalayas. Each term multiplies requests. |
| `hours_old` | JobSpy only: postings from the last N hours. |
| `sources.jobspy.searches` | Sites, location, Indeed country and remote flag per search. |
| `sources.jobspy.results_wanted` | Results per site and call (keep small; boards block scrapers). |
| `filters.*` | Stage 1 hard rules: role words in the title, excluded title words, other-stack titles without the core stack, on-site countries. |
| `scoring.zones` | `apply` (>= 85), `review` (70-84), `low`. Keep in sync with `ZONE_THRESHOLDS` in `src/lib/jobs-schema.ts` (a Vitest test checks it). |
| `scoring.min_score_to_keep` | Postings below this are not written. |
| `scoring.core_terms` | Core stack weights. |
| `scoring.adjustments` | Bonuses and penalties (remote abroad, region restriction, seniority, years, exclusions). |
| `scoring.eligible_regions` | A remote posting that states any location is "restricted" unless its location text contains one of these (worldwide, LatAm, Peru, US timezones...). |
| `synonyms` | Canonical tech terms and aliases. Keys match the profile tags. |
| `labels` | Display names used in reasons. |
| `output.prune_after_days` | Drop postings not seen for this many days. |

## Sources and their terms

Every request uses the generic `user_agent` from the config (no personal data).

| Source | Endpoint | Terms we honor |
|---|---|---|
| JobSpy (`python-jobspy`) | LinkedIn, Indeed (Peru and US remote), Google | Scraper; small `results_wanted`; each site's error is reported separately. Glassdoor is not configured because it does not cover Peru. |
| [Remotive](https://github.com/remotive-com/remote-jobs-api) | `GET https://remotive.com/api/remote-jobs?search=&limit=` | Link back to the job URL on Remotive and name Remotive as the source; at most ~4 calls a day and never more than 2 per minute (we sleep 31 s between terms); jobs are delayed 24 h; do not submit the jobs to other job boards. |
| [Remote OK](https://remoteok.com/api) | `GET https://remoteok.com/api` (one request, whole feed) | Link back to the job URL on Remote OK (follow, no `nofollow`) and name Remote OK as the source; do not use their logo. |
| [Himalayas](https://himalayas.app/api) | `GET https://himalayas.app/jobs/api/search?q=&page=` | Use `applicationLink` unchanged as the Apply link (`url`); show a visible link to the job on Himalayas (`attribution.url`); show jobs only on sites we operate; do not pass them to other boards; remove expired jobs (dropped on parse and on prune via `expires_at`). Terms: https://himalayas.app/terms#api |

Each job stores `source` and, for the API sources, `attribution: {name, url}`. The UI must show
"via <name>" linking to `attribution.url` without `rel="nofollow"`.

A source that throws is logged and recorded in `sources[].error`; the run continues with the others.

## Pipeline

1. **Fetch** each enabled source; normalize to `jobs/models.py:Job` (plain-text description trimmed
   to `max_description_chars`, ISO-2 `country` when the location names one, `market` = `peru` when
   the country is PE, else `abroad`).
2. **Dedupe** against the run and the previous `data/jobs.json`: same canonical URL (tracking
   parameters removed, identifying ones such as Indeed `jk` kept) or same normalized company + title.
   The merged posting keeps the oldest id and `first_seen`, updates `last_seen`, and keeps the
   richer description. Postings not seen for `prune_after_days`, or past `expires_at`, are dropped.
3. **Filter** (stage 1, `scoring.passes_filters`).
4. **Score** (stage 2, `scoring.score_job`) and write, sorted by score.

`id` is `job-` + the first 8 hex chars of the SHA-1 of the canonical URL, so it is stable across runs
and usable in `/tailor <job-id>`.

## How scoring works

- **Profile vocabulary**: every highlight tag in `data/profile.json` that is a known canonical term,
  weighted by how many highlights back it (verified = 1, partial = 0.5, saturating at
  `profile_saturation`), plus terms named in the skills section and project stacks (at least
  `skills_min_strength`).
- **Posting terms**: aliases from `synonyms` found on word boundaries. A term in the title weighs 3,
  in the description 1, only in a "nice to have / deseable / a plus" part 0.5.
- **Score** = 70 x coverage + 30 x core + adjustments, clamped to 0-100.
  - coverage: weighted share of posting terms the profile has (each scaled by profile strength);
    reduced for thin postings (`min_evidence_weight`).
  - core: summed `core_terms` weights present in the posting (.NET, C#, Azure, Angular, SQL Server).
  - adjustments: +5 remote abroad; -25 remote restricted to regions that exclude Peru/LatAm;
    -20 principal/staff/director titles; -5 junior titles; -10 when more than 6 years are required;
    -40 for exclusion phrases such as "US citizens only".
- `matched` / `missing`: posting terms the profile has / lacks, heaviest first.
- `reasons`: 2-4 short rule-generated English strings (stack match, remote/Peru, penalties, missing).
