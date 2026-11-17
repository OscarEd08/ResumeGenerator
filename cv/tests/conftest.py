"""Make `cv/` modules (build, tailor) and the repo-root `jobs` package importable from the tests."""

from __future__ import annotations

import sys
from pathlib import Path

CV_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = CV_DIR.parent

for path in (CV_DIR, REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
