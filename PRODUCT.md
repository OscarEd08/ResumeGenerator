# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Astro (static output), deployed to GitHub Pages as a public project site. Python (RenderCV, JobSpy) runs in GitHub Actions or locally; the site itself has no backend.

## Users

A single user: the owner, a .NET / Angular / Azure software developer based in Lima, Peru, actively looking for a new role. He reviews job matches and prepares tailored applications, mostly from a desktop PC where Claude Code runs.

## Product Purpose

A personal job-search cockpit with two jobs:

1. **Find jobs that fit.** A scheduled GitHub Action collects job postings (LinkedIn, Indeed, Glassdoor, remote-job APIs; Apify only for gaps such as Peruvian boards), filters them, and scores each against the owner's profile with reasons and gaps.
2. **Apply with a tailored CV.** For a selected job, a local Claude Code command (`/tailor <job-id>`) selects and rephrases verified bullets from the profile bank into a RenderCV YAML and renders an ATS-safe PDF. The site previews that PDF and offers it for download.

Success: less time per application, and CVs that pass ATS filters and match each posting without inventing experience. Priority targets are foreign companies (better pay), then Peruvian ones.

## Positioning

The CV content comes only from a verified profile bank built from the owner's own markdown records (with evidence levels); tailoring reorders and rephrases, never invents.

## Operating Context

- Source of truth: `docs/*.md` (experience records) → `data/profile.json` (bullet bank).
- Jobs: `data/jobs.json`, refreshed by a scheduled GitHub Action.
- Tailored CVs: RenderCV YAML → PDF + PNG under `public/cv/`.
- Daily loop: open the site, scan scored jobs, open a job detail, copy the `/tailor <job-id>` command, run it locally, review the CV preview, download the PDF, apply.
- Per-job status (new / applied / discarded) lives in the browser's localStorage.

## Capabilities and Constraints

- Static site only: no API keys or LLM calls from the browser.
- The site is public; that is accepted by the owner.
- Interface language: Spanish. CVs are generated in English or Spanish depending on the job.
- Screens planned: job list (filters, score, status), job detail (score reasons, matched/missing keywords, copy-tailor-command button, description), CV preview (embedded PDF, keyword coverage, download), base CV.
- Undecided: whether a GitHub Action (Claude API) will later trigger tailoring from the site.

## Brand Commitments

The owner asked for a modern, minimalist interface.

## Evidence on Hand

- Profile records: `docs/bertoni-experience.md`, `docs/cv-bertoni-proyectos.md`, `docs/cv-proyectos-personales.md`.
- Reference CV (layout and content): `docs/Oscar_Pairazaman_CV.pdf`.
- No real job data yet; do not fabricate job postings beyond clearly labeled fixtures.

## Product Principles

1. Truth over polish: never show or generate claims the profile bank cannot back.
2. Decision speed: the job list must make "worth applying?" answerable at a glance.
3. The CV preview is the real PDF; what you see is what the ATS reads.
4. Zero running cost by default; paid services only for named gaps.
