from pathlib import Path

import pytest
from rest_framework.test import APIClient

FIXTURES_DIR = Path(__file__).parents[2] / "fixtures"


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def job_offer_text():
    return (FIXTURES_DIR / "sample_job_offer.txt").read_text(encoding="utf-8")
