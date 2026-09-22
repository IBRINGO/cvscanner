import pytest
from django.urls import reverse
from rest_framework import status

from apps.documents.models import Document
from tests.api.cvs.conftest import make_upload


@pytest.mark.django_db
class TestCvProfile:
    def test_processed_document_returns_full_profile(self, api_client, cv_pdf_bytes):
        upload = api_client.post(
            reverse("cv-list-create"),
            {"file": make_upload("sample_cv.pdf", cv_pdf_bytes, "application/pdf")},
            format="multipart",
        )

        response = api_client.get(reverse("cv-profile", args=[upload.data["id"]]))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "PROCESSED"
        profile = response.data["profile"]
        assert profile["full_name"] == "Jordan Rivera"
        assert profile["email"] == "jordan.rivera@example.com"
        assert len(profile["experiences"]) == 2
        assert len(profile["skills"]) >= 1

    def test_skill_evidence_is_included_and_has_no_internal_ids(self, api_client, cv_pdf_bytes):
        upload = api_client.post(
            reverse("cv-list-create"),
            {"file": make_upload("sample_cv.pdf", cv_pdf_bytes, "application/pdf")},
            format="multipart",
        )

        response = api_client.get(reverse("cv-profile", args=[upload.data["id"]]))

        skill = next(s for s in response.data["profile"]["skills"] if s["raw_text"] == "Python")
        assert skill["skill"]["canonical_name"] == "Python"
        assert skill["evidence"]["section"] == "SKILLS"
        assert "id" not in skill["evidence"]
        assert "source_document" not in skill["evidence"]

    def test_experiences_carry_normalized_seniority_and_merged_technologies(self, api_client, cv_pdf_bytes):
        upload = api_client.post(
            reverse("cv-list-create"),
            {"file": make_upload("sample_cv.pdf", cv_pdf_bytes, "application/pdf")},
            format="multipart",
        )

        response = api_client.get(reverse("cv-profile", args=[upload.data["id"]]))

        experiences = response.data["profile"]["experiences"]
        senior_experience = next(e for e in experiences if e["title"] == "Senior Backend Engineer")
        assert senior_experience["seniority"] == "SENIOR"
        assert "Django" in senior_experience["technologies"]

    def test_education_carries_normalized_degree_level(self, api_client, cv_pdf_bytes):
        upload = api_client.post(
            reverse("cv-list-create"),
            {"file": make_upload("sample_cv.pdf", cv_pdf_bytes, "application/pdf")},
            format="multipart",
        )

        response = api_client.get(reverse("cv-profile", args=[upload.data["id"]]))

        education = response.data["profile"]["education"][0]
        assert education["degree_level"] == "BACHELOR"

    def test_language_carries_canonical_name_and_normalized_proficiency(self, api_client, cv_pdf_bytes):
        upload = api_client.post(
            reverse("cv-list-create"),
            {"file": make_upload("sample_cv.pdf", cv_pdf_bytes, "application/pdf")},
            format="multipart",
        )

        response = api_client.get(reverse("cv-profile", args=[upload.data["id"]]))

        english = next(lang for lang in response.data["profile"]["languages"] if lang["name"] == "English")
        assert english["canonical_name"] == "English"
        assert english["proficiency_normalized"] == "NATIVE"

    def test_no_match_or_compatibility_field_anywhere_in_response(self, api_client, cv_pdf_bytes):
        upload = api_client.post(
            reverse("cv-list-create"),
            {"file": make_upload("sample_cv.pdf", cv_pdf_bytes, "application/pdf")},
            format="multipart",
        )

        response = api_client.get(reverse("cv-profile", args=[upload.data["id"]]))

        body = str(response.data).lower()
        assert "match_score" not in body
        assert "compatibility" not in body
        assert "ats_score" not in body

    def test_unprocessed_document_returns_null_profile(self, api_client):
        # Bypasses the upload flow to freeze the document in UPLOADED -
        # exercises the "not ready yet" branch the frontend polls against.
        document = Document.objects.create(
            document_type="CV",
            original_filename="cv.pdf",
            mime_type="application/pdf",
            file_size=10,
            file_hash="y" * 64,
            storage_reference="cv/y.pdf",
            status="UPLOADED",
        )

        response = api_client.get(reverse("cv-profile", args=[document.id]))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "UPLOADED"
        assert response.data["profile"] is None
