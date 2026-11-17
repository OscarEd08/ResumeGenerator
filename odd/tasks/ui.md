# Feature: ui (contact-sheet job cockpit)

Objective: build the Astro UI in the chosen "Hoja de contactos" direction over real `data/jobs.json`, `data/profile.json` and `public/cv/*.pdf`.
Branch: `feat/ui` (from `feat/job-search`) · Delivery: ask-on-risk · Runners: Vitest, astro build, impeccable detect + finish review.

## Specs

- **S1** Screens: job list (filters, score, status), job detail (score reasons, matched/missing keywords, copy `/tailor <job-id>` button, description), CV preview ("Me gustaría que se pueda ver una preview del cv generado"), base CV.
- **S2** Direction: `.impeccable/surfaces/src-pages-index-astro.md` direction contract (contact sheet), chosen sketch `.impeccable/mocks/decision/r1-assigned.html`; "algo moderno y minimalista"; no blue, red or Claude colors; not a corporate dashboard, not a generic AI template, not decorative, comfortable on a phone.
- **S3** Status per job (nueva / preseleccionada / postulada / descartada) in localStorage; site works when storage is unavailable.
- **S4** Source attribution: API jobs show "via <name>" linking to `attribution.url` without `rel="nofollow"`; Himalayas apply link is `url`/applicationLink unchanged.
- **S5** Spanish UI copy.

## Tasks

| ID | Specs | Route | Status | Commit |
|---|---|---|---|---|
| T1 | S1–S5 | delegated (context backstop: parent context is long) | pending | |
| T2 | S2 | finish review (impeccable-finish-reviewer) + DESIGN.md (impeccable-documenter) | pending | |

## Log

- **L1** (2026-11-16) Plan approved earlier: steps 1 repo/profile, 2 base CV, 3 /tailor, 4 job search, 5 UI with impeccable. User chose the contact-sheet card on the decision page; user constraints: "no me gusta el azul en los diseños, ni tampoco los colores de Claude o rojos".
