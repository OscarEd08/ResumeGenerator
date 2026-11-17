# CV generator (RenderCV)

`cv/base.yaml` is the base CV: a RenderCV input that reproduces `docs/Oscar_Pairazaman_CV.pdf`.

## Setup (from the repo root)

    python -m venv .venv
    .venv/Scripts/python -m pip install -r cv/requirements.txt   # Windows (use .venv/bin/python on Linux/macOS)

## Build

    .venv/Scripts/python cv/build.py cv/base.yaml [--out public/cv]

Writes `<name>.pdf` and `<name>_<page>.png` to `--out` (default `public/cv/`). Typst intermediates go to a temp dir; no HTML/Markdown.

## Test (ATS text-layer checks)

    .venv/Scripts/python -m pytest cv/tests -q

Windows note: RenderCV crashes on cp1252 consoles. `build.py` forces `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` for the child process; set them yourself if you call `rendercv` directly.
