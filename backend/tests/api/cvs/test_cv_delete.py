import pytest
from django.urls import reverse
from rest_framework import status

from apps.documents.models import Document
from tests.api.cvs.conftest import make_upload


@pytest.mark.django_db
class TestCvDelete:
    def test_deletes_a_processed_cv(self, api_client, cv_pdf_bytes):
        upload = api_client.post(
            reverse("cv-list-create"),
            {"file": make_upload("sample_cv.pdf", cv_pdf_bytes, "application/pdf")},
            format="multipart",
        )
        document_id = upload.data["id"]

        response = api_client.delete(reverse("cv-detail", args=[document_id]))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Document.objects.filter(id=document_id).exists()

    def test_deleted_cv_no_longer_appears_in_the_list(self, api_client, cv_pdf_bytes):
        upload = api_client.post(
            reverse("cv-list-create"),
            {"file": make_upload("sample_cv.pdf", cv_pdf_bytes, "application/pdf")},
            format="multipart",
        )
        document_id = upload.data["id"]
        api_client.delete(reverse("cv-detail", args=[document_id]))

        response = api_client.get(reverse("cv-list-create"))

        assert all(doc["id"] != document_id for doc in response.data)

    def test_deleting_a_cv_lets_the_exact_same_file_be_uploaded_again(self, api_client, cv_pdf_bytes):
        # The whole point of this feature: dedup-by-hash (see
        # application/documents/upload_document.py) would otherwise
        # silently reuse the old (possibly stale) Document forever.
        first_upload = api_client.post(
            reverse("cv-list-create"),
            {"file": make_upload("sample_cv.pdf", cv_pdf_bytes, "application/pdf")},
            format="multipart",
        )
        first_id = first_upload.data["id"]
        api_client.delete(reverse("cv-detail", args=[first_id]))

        second_upload = api_client.post(
            reverse("cv-list-create"),
            {"file": make_upload("sample_cv.pdf", cv_pdf_bytes, "application/pdf")},
            format="multipart",
        )

        assert second_upload.status_code == status.HTTP_202_ACCEPTED
        assert second_upload.data["id"] != first_id
        assert Document.objects.filter(id=second_upload.data["id"]).exists()

    def test_deleting_an_unknown_cv_returns_404(self, api_client):
        response = api_client.delete(
            reverse("cv-detail", args=["00000000-0000-0000-0000-000000000000"])
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_delete_a_job_offer_through_the_cv_endpoint(self, api_client):
        job_upload = api_client.post(
            reverse("job-list-create"), {"text": "Some job offer text."}, format="json"
        )
        response = api_client.delete(reverse("cv-detail", args=[job_upload.data["id"]]))

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Document.objects.filter(id=job_upload.data["id"]).exists()
