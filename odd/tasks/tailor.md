# Feature: tailor

Objective: a local Claude Code command `/tailor <job-id>` that turns one scored job into a tailored, ATS-safe CV (PDF + page PNGs) that the site already previews.
Branch: `feat/tailor` (stacked on `feat/ui`). Delivery: ask-on-risk. Test runners: `.venv/Scripts/python -m pytest cv/tests -q` and `npm test`.

## Specs

- **S1. Tailored to the job.** The user's request, verbatim: "La idea es que el CV que se genere se adapte al puesto que estaría aplicando." `/tailor <job-id>` reads the job from `data/jobs.json` and the bank from `data/profile.json`. It selects and orders the bullets that best cover the job's keywords and adjusts the summary and skills to match.
- **S2. Never invent.** Every experience bullet comes from a bank highlight, cited by its `id`. It is either verbatim or rephrased without adding technologies, numbers or claims that the highlight does not contain. The `❓` claims are already excluded from the bank and must stay out. A deterministic check rejects any bullet id that is not in the bank.
- **S3. Same template.** Uses `cv/base.yaml`'s design (RenderCV, `engineeringresumes`, XCharter), the same layout as `docs/Oscar_Pairazaman_CV.pdf`. Maximum 2 pages.
- **S4. ATS.** The output must pass ATS filters: the text extracts in reading order with pypdf, there is no table or image text, and section headings are standard. It reuses the checks in `cv/tests/test_ats.py`.
- **S5. Language by market.** English for jobs abroad and Spanish for Peru, using `text_es`.
- **S6. Output the site already reads.** Writes `public/cv/<job-id>.pdf` plus `<job-id>_<n>.png` via `cv/build.py`, which `src/lib/ui/cvs.ts` lists and `/cv/[id]` previews. Keeps the tailored input at `cv/tailored/<job-id>.yaml`.
- **S7. Report.** At the end, prints the keywords covered and those still missing, the page count, and the paths.
- **S8. Trigger.** Option B, as decided earlier: the site's button copies `/tailor <job-id>`, which the user runs locally in Claude Code at no extra cost.

## Tasks

- [x] T1 — S1–S8 — delegated (user asked: "manda a un agente a avanzarlo") — commit: 9417cab

## Log

- L1 (2026-11-17) User, verbatim: "si dale manda a un agente a avanzarlo."
- L2 Context: the button already exists (TailorCommand). `/cv/[id]` expects `public/cv/<job-id>.pdf` plus PNGs. Jobs are pruned after 30 days, so a tailored CV must still render with a sensible title once its job leaves `data/jobs.json`.
- L3 (2026-11-17) T1 implemented by the delegated writer. Design: `cv/tailor.py` (`context` / `build`) plus `.claude/commands/tailor.md`. The ATS checks moved into `cv/build.py` (`check_*`, `ats_problems`); `test_ats.py` and `tailor.py` both call them (S4). A bullet cites one or more bank ids of the same entry, verbatim or with a `text`. `build` rejects unknown, cross-entry and duplicate ids, `❓`, and rephrasings whose numbers or tech terms (via `jobs/scoring.find_terms`) are not in the cited sources (S2). Keyword logic reuses `jobs/scoring.py`; PyYAML is absent from `.venv`, so a `ruamel.yaml` shim stands in. Verified: both load `jobs/config.yaml` identically. Rendering goes to a staging dir and is published to `public/cv` only after the ATS checks pass and the CV is at most 2 pages (S3, S6). Sidecar `cv/tailored/<id>.meta.json` keeps the title and company; `src/lib/ui/cvs.ts` falls back to it when the job is pruned.
- L4 Verification (RED observed first for pytest and Vitest):
  - `.venv/Scripts/python -m pytest cv/tests -q`: 33 passed.
  - `npm test`: 63 passed.
  - `npm run build`: 123 pages; `/cv/job-b9c6199b` built.
  - Demo `/tailor job-b9c6199b` (highest score, 93, abroad, English): Covered keywords: Angular, .NET, C#, REST APIs, SQL Server (5/5). Missing: none. Pages: 2. Outputs: `cv/tailored/job-b9c6199b.{selection.json,yaml,meta.json}` and `public/cv/job-b9c6199b.pdf` with `_1.png` and `_2.png`.
  - A Spanish run of the test fixture also rendered 2 pages with Spanish headings and dates.
- L5 Open: the tailored YAML and PDF carry the contact email copied from `cv/base.yaml`, the same as the base CV.
