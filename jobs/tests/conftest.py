import json
from datetime import date
from pathlib import Path

import pytest

from jobs.config import load_config

FIXTURES = Path(__file__).parent / "fixtures"
TODAY = date(2026, 11, 16)


def load_fixture(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture
def cfg():
    return load_config()


@pytest.fixture
def profile():
    return load_fixture("profile_min.json")


@pytest.fixture
def today():
    return TODAY
