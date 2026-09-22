from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parents[3] / "fixtures"


@pytest.fixture
def fixture_bytes():
    def _read(name: str) -> bytes:
        return (FIXTURES_DIR / name).read_bytes()

    return _read
