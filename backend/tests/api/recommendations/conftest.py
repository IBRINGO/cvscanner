from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient

FIXTURES_DIR = Path(__file__).parents[2] / "fixtures"


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
