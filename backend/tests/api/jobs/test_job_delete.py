from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from apps.documents.models import Document

FIXTURES_DIR = Path(__file__).parents[2] / "fixtures"


@pytest.mark.django_db
class TestJobDelete:
    def test_deletes_a_processed_job_offer(self, api_client, job_offer_text):
        upload = api_client.post(reverse("job-list-create"), {"text": job_offer_text}, format="json")
        document_id = upload.data["id"]

        response = api_client.delete(reverse("job-detail", args=[document_id]))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Document.objects.filter(id=document_id).exists()

    def test_deleted_job_no_longer_appears_in_the_list(self, api_client, job_offer_text):
        upload = api_client.post(reverse("job-list-create"), {"text": job_offer_text}, format="json")
        document_id = upload.data["id"]
        api_client.delete(reverse("job-detail", args=[document_id]))

        response = api_client.get(reverse("job-list-create"))

        assert all(doc["id"] != document_id for doc in response.data)

    def test_deleting_a_job_lets_the_exact_same_text_be_uploaded_again(self, api_client, job_offer_text):
        first_upload = api_client.post(reverse("job-list-create"), {"text": job_offer_text}, format="json")
        first_id = first_upload.data["id"]
        api_client.delete(reverse("job-detail", args=[first_id]))

        second_upload = api_client.post(reverse("job-list-create"), {"text": job_offer_text}, format="json")

        assert second_upload.status_code == status.HTTP_202_ACCEPTED
        assert second_upload.data["id"] != first_id

    def test_deleting_an_unknown_job_returns_404(self, api_client):
        response = api_client.delete(
            reverse("job-detail", args=["00000000-0000-0000-0000-000000000000"])
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_delete_a_cv_through_the_job_endpoint(self, api_client):
        content = (FIXTURES_DIR / "sample_cv.pdf").read_bytes()
        cv_upload = api_client.post(
            reverse("cv-list-create"),
            {"file": SimpleUploadedFile("sample_cv.pdf", content, content_type="application/pdf")},
            format="multipart",
        )

        response = api_client.delete(reverse("job-detail", args=[cv_upload.data["id"]]))

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Document.objects.filter(id=cv_upload.data["id"]).exists()
