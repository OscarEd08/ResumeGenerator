"""Render a RenderCV YAML file to PDF + PNG pages.

Usage:
    python cv/build.py <input.yaml> [--out <dir>]

Outputs `<stem>.pdf` and `<stem>_<page>.png` into --out (default: public/cv/).
The Typst intermediate is written to a temporary directory and discarded;
Markdown and HTML outputs are not generated.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "public" / "cv"


def utf8_env() -> dict[str, str]:
    """RenderCV crashes on Windows cp1252 consoles unless Python runs in UTF-8 mode."""
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def build(input_yaml: Path, out_dir: Path) -> list[Path]:
    input_yaml = input_yaml.resolve()
    if not input_yaml.is_file():
        raise FileNotFoundError(f"Input file not found: {input_yaml}")
    stem = input_yaml.stem
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="rendercv_") as tmp:
        tmp_dir = Path(tmp)
        command = [
            sys.executable, "-m", "rendercv", "render", str(input_yaml),
            "--typst-path", str(tmp_dir / f"{stem}.typ"),
            "--pdf-path", str(tmp_dir / f"{stem}.pdf"),
            "--png-path", str(tmp_dir / f"{stem}.png"),
            "--dont-generate-markdown",
            "--dont-generate-html",
            "--quiet",
        ]
        result = subprocess.run(
            command, env=utf8_env(), capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        pdf = tmp_dir / f"{stem}.pdf"
        if result.returncode != 0 or not pdf.is_file():
            raise RuntimeError(
                f"RenderCV failed (exit {result.returncode}):\n{result.stdout}\n{result.stderr}"
            )

        # Remove stale outputs of this CV (e.g. a page that no longer exists).
        for old in [out_dir / f"{stem}.pdf", *out_dir.glob(f"{stem}_*.png")]:
            old.unlink(missing_ok=True)

        produced = [pdf, *sorted(tmp_dir.glob(f"{stem}_*.png"))]
        return [Path(shutil.copy2(path, out_dir / path.name)) for path in produced]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a RenderCV YAML file to PDF + PNG.")
    parser.add_argument("input", type=Path, help="RenderCV YAML input file")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"output directory (default: {DEFAULT_OUT})")
    args = parser.parse_args(argv)
    try:
        files = build(args.input, args.out)
    except (FileNotFoundError, RuntimeError) as error:
        print(error, file=sys.stderr)
        return 1
    for path in files:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
