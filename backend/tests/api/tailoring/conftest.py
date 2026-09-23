from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient

FIXTURES_DIR = Path(__file__).parents[2] / "fixtures"


class _AlwaysSimilarEmbeddingProvider:
    """Test-only stub: every embedding is identical, so cosine similarity
    is always 1.0. `config.settings.testing` blanks both real API keys,
    so the real analysis/tailoring pipeline otherwise uses
    FakeEmbeddingProvider, whose vectors are explicitly documented as
    semantically meaningless - responsibility matching would then almost
    never reach SEMANTIC_MATCH, and these tailoring tests need at least
    one deterministic SAFE_TO_REPHRASE recommendation to exercise the
    AGGRESSIVE_SAFE path end to end.
    """

    name = "test-stub"
    dimensions = 4

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0, 0.0, 0.0] for _ in texts]


@pytest.fixture(autouse=True)
def force_semantic_responsibility_matches(monkeypatch):
    monkeypatch.setattr(
        "config.container.build_embedding_provider", lambda: _AlwaysSimilarEmbeddingProvider()
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def processed_cv_id(api_client) -> str:
    content = (FIXTURES_DIR / "sample_cv.pdf").read_bytes()
    upload = SimpleUploadedFile("sample_cv.pdf", content, content_type="application/pdf")
    response = api_client.post(reverse("cv-list-create"), {"file": upload}, format="multipart")
    return response.data["id"]


@pytest.fixture
def processed_job_id(api_client) -> str:
    text = (FIXTURES_DIR / "sample_job_offer.txt").read_text(encoding="utf-8")
    response = api_client.post(reverse("job-list-create"), {"text": text}, format="json")
    return response.data["id"]


@pytest.fixture
def completed_analysis_id(api_client, processed_cv_id, processed_job_id) -> str:
    response = api_client.post(
        reverse("analysis-list-create"),
        {"candidate_document_id": processed_cv_id, "job_document_id": processed_job_id},
        format="json",
    )
    return response.data["id"]


@pytest.fixture
def safe_recommendation_ids(api_client, completed_analysis_id) -> list[str]:
    response = api_client.get(reverse("analysis-recommendations", args=[completed_analysis_id]))
    return [r["id"] for r in response.data if r["safe_to_tailor"]]
