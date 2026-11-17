# Feature: foundation (profile bank + base CV)

Objective: Astro site skeleton + structured profile bank from `docs/*.md`, and a RenderCV base CV that reproduces `docs/Oscar_Pairazaman_CV.pdf`.
Branch: `feat/foundation` · Delivery: ask-on-risk · Runners: Vitest (Node/Astro), pytest (Python/RenderCV).

## Specs

- **S1** Source of truth: "En la carpeta docs tengo archivos markdowns que describen mi experiencia laboral en Bertoni ... La idea es que estos archivos sean por ahora la fuente de verdad y que sean actualizables con todo lo nuevo. En un futuro se podria mejorar los nombres de los archivos, agregar de otros lugares donde trabajé." → `docs/*.md` are converted into a structured bank `data/profile.json` validated by a schema; bullets carry ids, tags and evidence level; claims marked ❓ are excluded.
- **S2** Web stack: "Todo esto se debe ver en una web que subire a github pages" + "Que sea con Astro." → Astro static site at repo root, configured for GitHub Pages, minimal placeholder page (real UI comes later with impeccable).
- **S3** Template: "En la carpeta de docs tengo un CV mio para que sirva de ejemplo y la plantilla de como quiero los CVs." + user chose "rendercv" → `cv/base.yaml` rendered by RenderCV reproduces the layout and content of `docs/Oscar_Pairazaman_CV.pdf`.
- **S4** ATS: "sobretodo por los filtros ATS que normalmente la mayoria lo usa" → automated test extracts text from the generated PDF and asserts logical reading order and complete content.

## Tasks

| ID | Specs | Route | Status | Commit |
|---|---|---|---|---|
| T1 | S1, S2 | delegated (user asked for two agents; parallel disjoint units) | done (10 vitest pass, build ok) | see log L6 |
| T2 | S3, S4 | delegated (user asked for two agents; parallel disjoint units) | done (9 ATS tests pass) | 3aa3a5f |

## Log

- **L1** (2026-11-16) User original request: "En este proyecto quiero trabajar dos cosas: un generador de CV y un buscador de empleo en base a mi perfil. ... Asi que ayudame a ordernar mejor todo esto y definir como se lograría" (full text in conversation; key quotes in S1–S4).
- **L2** Decisions: public site OK; Astro; tailor option B (local `/tailor <job-id>`); RenderCV for PDFs; job search via JobSpy + free APIs, Apify only for gaps.
- **L3** User: "si manda a dos agentes a hacerlos. Te doy liberta de correr los comandos de impeccable"
- **L4** RenderCV 2.8 probe: theme `engineeringresumes`, XCharter, custom `templates.experience_entry` matches the PDF; set `show_top_note: false`, international phone format, left alignment, uppercase section titles. Windows needs `PYTHONUTF8=1`.
- **L5** T2 done: cv/base.yaml reproduces the PDF in 2 pages; remaining diffs: page break position, LinkedIn on same line, heavier black section rules, smaller bullet glyph. pytest 9 passed (parent spot check).
- **L6** T1 done: data/profile.json (5 experience, 1 project, 89 highlights, 5 partial; ❓ excluded: 500k SKUs, 6-7s->1s search). Commits: feat(profile) + ci (Risk item 5, action tags verified with git ls-remote). Open content questions: ai-standards numbers conflict between docs (newer doc used), Cloud Store 40% unbacked (kept without number), older jobs verified only by owner's word. Pages source must be set to GitHub Actions.
