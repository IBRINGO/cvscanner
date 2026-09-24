"""End-to-end API tests for job offer ingestion (sections 23, 31-33, 73
of the Phase 2 brief). Covers the "plain text" submission path, which is
job-offer-specific (CVs are not commonly pasted as raw text).
"""
import pytest
from django.urls import reverse
from rest_framework import status

from apps.documents.models import Document
from apps.jobs.models import JobProfile


@pytest.mark.django_db
class TestJobUpload:
    def test_plain_text_job_offer_is_accepted_and_processed(self, api_client, job_offer_text):
        response = api_client.post(reverse("job-list-create"), {"text": job_offer_text}, format="json")

        assert response.status_code == status.HTTP_202_ACCEPTED
        document = Document.objects.get(id=response.data["id"])
        assert document.status == "PROCESSED"
        assert document.document_type == "JOB_OFFER"

    def test_pasted_text_is_renamed_to_the_extracted_job_title(self, api_client, job_offer_text):
        # sample_job_offer.txt's first line is "Senior Backend Engineer" -
        # the placeholder "job-offer.txt" name every pasted submission
        # starts with should be replaced by that once extraction runs.
        response = api_client.post(reverse("job-list-create"), {"text": job_offer_text}, format="json")

        document = Document.objects.get(id=response.data["id"])
        assert document.original_filename == "Senior Backend Engineer"

        list_response = api_client.get(reverse("job-list-create"))
        listed = next(doc for doc in list_response.data if doc["id"] == str(document.id))
        assert listed["original_filename"] == "Senior Backend Engineer"

    def test_processed_profile_distinguishes_required_and_preferred(self, api_client, job_offer_text):
        upload = api_client.post(reverse("job-list-create"), {"text": job_offer_text}, format="json")

        response = api_client.get(reverse("job-profile", args=[upload.data["id"]]))

        requirements = response.data["profile"]["requirements"]
        required_skills = {
            r["skill"]["canonical_name"] for r in requirements if r["importance"] == "REQUIRED" and r["skill"]
        }
        preferred_skills = {
            r["skill"]["canonical_name"]
            for r in requirements
            if r["importance"] == "PREFERRED" and r["skill"]
        }

        assert "Python" in required_skills
        assert "Amazon Web Services" in preferred_skills

    def test_no_match_score_or_compatibility_field_anywhere_in_response(self, api_client, job_offer_text):
        upload = api_client.post(reverse("job-list-create"), {"text": job_offer_text}, format="json")
        response = api_client.get(reverse("job-profile", args=[upload.data["id"]]))

        body = str(response.data).lower()
        assert "match_score" not in body
        assert "compatibility" not in body
        assert "ats_score" not in body

    def test_empty_submission_is_rejected(self, api_client):
        response = api_client.post(reverse("job-list-create"), {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_duplicate_text_reuses_document(self, api_client, job_offer_text):
        first = api_client.post(reverse("job-list-create"), {"text": job_offer_text}, format="json")
        second = api_client.post(reverse("job-list-create"), {"text": job_offer_text}, format="json")

        assert first.data["id"] == second.data["id"]
        assert JobProfile.objects.count() == 1
