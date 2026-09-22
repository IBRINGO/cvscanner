import pytest
from django.urls import reverse
from rest_framework import status

from apps.documents.models import Document


@pytest.mark.django_db
class TestCvStatus:
    def test_status_reflects_processed_document(self, api_client, cv_pdf_bytes):
        from tests.api.cvs.conftest import make_upload

        upload = api_client.post(
            reverse("cv-list-create"),
            {"file": make_upload("sample_cv.pdf", cv_pdf_bytes, "application/pdf")},
            format="multipart",
        )
        document_id = upload.data["id"]

        response = api_client.get(reverse("cv-status", args=[document_id]))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "PROCESSED"
        assert response.data["error"] is None

    def test_status_reports_failure_reason_for_failed_document(self, api_client, corrupted_pdf_bytes):
        from tests.api.cvs.conftest import make_upload

        upload = api_client.post(
            reverse("cv-list-create"),
            {"file": make_upload("corrupted.pdf", corrupted_pdf_bytes, "application/pdf")},
            format="multipart",
        )

        response = api_client.get(reverse("cv-status", args=[upload.data["id"]]))

        assert response.data["status"] == "FAILED"
        assert response.data["error"]
        assert "Traceback" not in response.data["error"]  # no stack trace leakage (section 30)

    def test_unknown_document_id_returns_404(self, api_client):
        response = api_client.get(reverse("cv-status", args=["00000000-0000-0000-0000-000000000000"]))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_job_document_id_is_not_visible_through_cv_endpoint(self, api_client):
        # A JOB_OFFER document must not be readable via /cvs/ - resources
        # are strictly scoped by document_type.
        job_document = Document.objects.create(
            document_type="JOB_OFFER",
            original_filename="job.txt",
            mime_type="text/plain",
            file_size=10,
            file_hash="x" * 64,
            storage_reference="job_offer/x.txt",
        )

        response = api_client.get(reverse("cv-status", args=[job_document.id]))

        assert response.status_code == status.HTTP_404_NOT_FOUND
