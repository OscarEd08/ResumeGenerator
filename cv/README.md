# CV generator (RenderCV)

`cv/base.yaml` is the base CV: a RenderCV input that reproduces `docs/Oscar_Pairazaman_CV.pdf`.

## Setup (from the repo root)

    python -m venv .venv
    .venv/Scripts/python -m pip install -r cv/requirements.txt   # Windows (use .venv/bin/python on Linux/macOS)

## Build

    .venv/Scripts/python cv/build.py cv/base.yaml [--out public/cv]

Writes `<name>.pdf` and `<name>_<page>.png` to `--out` (default `public/cv/`). Typst intermediates go to a temp dir; no HTML/Markdown.

## Test (ATS text-layer checks and tailoring)

    .venv/Scripts/python -m pytest cv/tests -q

Windows note: RenderCV crashes on cp1252 consoles. `build.py` forces `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` for the child process; set them yourself if you call `rendercv` directly.

## Tailored CVs (`/tailor <job-id>`)

The site's job page copies `/tailor <job-id>`. Run it in Claude Code from the repo root. The command (`.claude/commands/tailor.md`) drives `cv/tailor.py`:

    .venv/Scripts/python cv/tailor.py context <job-id>   # job + bank bullets ranked by the job's keywords (JSON)
    # Claude writes cv/tailored/<job-id>.selection.json (summary, bullet ids, optional rephrasing, skills order)
    .venv/Scripts/python cv/tailor.py build <job-id>     # validate, write YAML, render, ATS + 2-page check, report
    .venv/Scripts/python cv/tailor.py letter <job-id>    # cover letter from cv/tailored/<job-id>.letter.json: 1 page, same header and font
    .venv/Scripts/python cv/tailor.py publish <job-id>   # commit only this CV's files and push to origin/main (rebases over the job bot)

`build` does the following:

- It rejects bullets that cite an id that is not in `data/profile.json` or that belongs to another entry. It also rejects rephrasings that add numbers or technologies their cited highlights do not contain, and summaries that name technologies the bank does not back.
- It writes `cv/tailored/<job-id>.yaml` with `base.yaml`'s header, entry headers, design and layout. Only the summary, bullets and skills change.
- It picks the language from the job's `market`: English for jobs abroad, Spanish (`text_es`, Spanish headings and dates) for Peru.
- It renders into a staging directory. Then it runs the same ATS checks as `cv/tests/test_ats.py` (the `check_*` functions in `build.py`) and enforces a maximum of 2 pages. Only then does it publish `public/cv/<job-id>.pdf` and `<job-id>_<n>.png`.
- It writes `cv/tailored/<job-id>.meta.json` (title, company, file name, coverage). The site uses it to title the CV after the job is pruned from `jobs.json`, and to download it under the readable name.
- It copies the PDF to `cv/out/Oscar_Pairazaman_CV_<Company>.pdf` (git-ignored), ready to attach. If another job's CV for the same company already took that name, the role is appended. The first output line, `CV: <path>`, names that file.
- The ATS check finds a bullet even when the PDF wraps it at a hyphen (`image-to-` / `PDF`).
- It prints the covered and missing keywords, the page count and the file paths.

Options for testing or other inputs: `--jobs`, `--profile`, `--selection`, `--tailored-dir`, `--out` and `--named-dir`.

Keyword matching reuses `jobs/scoring.py` and `jobs/config.yaml`. That code loads YAML with PyYAML, which this venv does not install, so `tailor.py` passes it `ruamel.yaml`'s safe loader instead. Both read the config identically.

## Cover letters (`/cover-letter <job-id>`)

When an application asks for a cover letter, run `/cover-letter <job-id>` in Claude Code. The job page has a button that copies it. The command (`.claude/commands/cover-letter.md`):

1. Writes `cv/tailored/<job-id>.letter.json`: greeting, 3-4 paragraphs and a closing, in the CV's language.
2. Runs `tailor.py letter`. It rejects technologies or numbers that are not in the bank, the same rule as the CV summary, and renders one US Letter page with `cv/letter.py`, using Typst and the CV's XCharter font and header. It also checks that the PDF text reads in order.
3. Writes `public/cv/letters/<job-id>.pdf`. The site shows a "Descargar carta" button on that job's CV page.
4. Copies the letter to `cv/out/Oscar_Pairazaman_Cover_Letter_<Company>.pdf`, or `..._Carta_Presentacion_...` in Spanish, ready to attach.
5. Publishes it to `main` with `tailor.py publish`.
