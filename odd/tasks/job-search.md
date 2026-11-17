# Feature: job-search (automated job discovery + scoring)

Objective: a scheduled pipeline that collects job postings, scores them against `data/profile.json`, and publishes `data/jobs.json` for the Astro site.
Branch: `feat/job-search` (from `feat/foundation`) · Delivery: ask-on-risk · Runners: pytest (pipeline), Vitest (schema of data/jobs.json).

## Specs

- **S1** Search: "Quiero que pueda buscar empleos que encajen muy bien con mi perfil." + "Mi objetivo es postular tanto a empresas peruanas como del extranjero (sobretodo estas porque son las que más pagan)." → sources: JobSpy (LinkedIn, Indeed, Glassdoor/Google where supported) for Peru and remote, plus free remote-job APIs; Apify is out of scope (only for later gaps).
- **S2** Fit scoring: jobs "que encajen muy bien con mi perfil" → stage 1 filter by rules (location/remote, stack, exclusions), stage 2 deterministic score 0–100 against profile tags with matched and missing keywords and short reasons. Zero running cost (PRODUCT.md principle 4): no paid LLM in the pipeline.
- **S3** Automation: "busqueda automatizada de trabajos" → GitHub Actions cron writes `data/jobs.json` and triggers the Pages deploy.
- **S4** UI contract: `data/jobs.json` validated by a zod schema used by the Astro site; each job has a stable id usable in `/tailor <job-id>`.

## Tasks

| ID | Specs | Route | Status | Commit |
|---|---|---|---|---|
| T1 | S1–S4 | delegated (user: "manda a un agente a hacerlo") | done (38 pytest, 17 vitest; S3 untested on GitHub) | feat(jobs) + ci commits |

## Log

- **L1** (2026-11-16) User: "si dale, manda a un agente a hacerlo" answering "¿Avanzo primero con el buscador automático (JobSpy en GitHub Actions + scoring), para que la interfaz se construya con datos reales?"
- **L2** Decision (parent): deterministic scoring to keep zero cost; LLM re-scoring deferred.
- **L3** T1 done: live run 119 jobs (apply 2, review 6, low 111); sources Remotive, RemoteOK, Himalayas, JobSpy LinkedIn/Indeed (LinkedIn 429 partial, Google 0). Attribution 'via <name>' links required in UI without nofollow; Himalayas apply link must be applicationLink. CI Python 3.13. Cron workflow untested until merged to main (Risk item 5).
