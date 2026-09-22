from pathlib import Path

import pytest

from domain.skills.normalization import build_alias_index
from domain.skills.taxonomy import SEED_SKILLS

FIXTURES_DIR = Path(__file__).parents[3] / "fixtures"


@pytest.fixture
def fixture_bytes():
    def _read(name: str) -> bytes:
        return (FIXTURES_DIR / name).read_bytes()

    return _read


@pytest.fixture
def skill_alias_index():
    return build_alias_index(SEED_SKILLS)
