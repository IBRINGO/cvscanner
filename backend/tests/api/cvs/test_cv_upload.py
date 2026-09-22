"""End-to-end API tests for CV upload (sections 8, 31-33, 72, 74-75 of
the Phase 2 brief). CELERY_TASK_ALWAYS_EAGER (config/settings/testing.py)
means the upload request also runs the full processing pipeline
synchronously, so the acceptance-test scenario in section 72 can be
verified in a single request/response cycle without a running worker.
"""
import pytest
from django.urls import reverse
from rest_framework import status

from apps.candidates.models import CandidateProfile
from apps.documents.models import Document
from tests.api.cvs.conftest import make_upload


@pytest.mark.django_db
class TestCvUpload:
    def test_valid_pdf_is_accepted_and_fully_processed(self, api_client, cv_pdf_bytes):
        response = api_client.post(
            reverse("cv-list-create"),
            {"file": make_upload("sample_cv.pdf", cv_pdf_bytes, "application/pdf")},
            format="multipart",
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        document_id = response.data["id"]

        document = Document.objects.get(id=document_id)
        assert document.status == "PROCESSED"
        assert document.document_type == "CV"
        assert CandidateProfile.objects.filter(document=document).exists()

    def test_valid_docx_is_accepted(self, api_client, cv_docx_bytes):
        response = api_client.post(
            reverse("cv-list-create"),
            {
                "file": make_upload(
                    "sample_cv.docx",
                    cv_docx_bytes,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
            format="multipart",
        )

        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_unsupported_file_type_is_rejected(self, api_client, unsupported_bytes):
        response = api_client.post(
            reverse("cv-list-create"),
            {"file": make_upload("unsupported.exe", unsupported_bytes, "application/x-msdownload")},
            format="multipart",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not Document.objects.exists()

    def test_missing_file_is_rejected(self, api_client):
        response = api_client.post(reverse("cv-list-create"), {}, format="multipart")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_corrupted_pdf_reaches_failed_status_without_crashing(self, api_client, corrupted_pdf_bytes):
        response = api_client.post(
            reverse("cv-list-create"),
            {"file": make_upload("corrupted.pdf", corrupted_pdf_bytes, "application/pdf")},
            format="multipart",
        )

        # Upload itself is accepted (format/size/mime are all fine) -
        # only the actual parsing fails.
        assert response.status_code == status.HTTP_202_ACCEPTED
        document = Document.objects.get(id=response.data["id"])
        assert document.status == "FAILED"
        assert document.processing_metadata.get("error")

    def test_uploading_the_same_file_twice_reuses_the_document(self, api_client, cv_pdf_bytes):
        first = api_client.post(
            reverse("cv-list-create"),
            {"file": make_upload("sample_cv.pdf", cv_pdf_bytes, "application/pdf")},
            format="multipart",
        )
        second = api_client.post(
            reverse("cv-list-create"),
            {"file": make_upload("sample_cv_copy.pdf", cv_pdf_bytes, "application/pdf")},
            format="multipart",
        )

        assert first.data["id"] == second.data["id"]
        assert Document.objects.filter(document_type="CV").count() == 1

    def test_list_returns_uploaded_documents(self, api_client, cv_pdf_bytes):
        api_client.post(
            reverse("cv-list-create"),
            {"file": make_upload("sample_cv.pdf", cv_pdf_bytes, "application/pdf")},
            format="multipart",
        )

        response = api_client.get(reverse("cv-list-create"))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_response_never_exposes_storage_reference(self, api_client, cv_pdf_bytes):
        response = api_client.post(
            reverse("cv-list-create"),
            {"file": make_upload("sample_cv.pdf", cv_pdf_bytes, "application/pdf")},
            format="multipart",
        )

        assert "storage_reference" not in response.data
