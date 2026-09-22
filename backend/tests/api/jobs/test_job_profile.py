"""API tests for Phase 3 semantic enrichment surfaced on the job profile
endpoint. See tests/api/jobs/test_job_upload.py for Phase 2 coverage of
the same endpoint.
"""
import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestJobProfileEnrichment:
    def test_seniority_is_normalized(self, api_client, job_offer_text):
        upload = api_client.post(reverse("job-list-create"), {"text": job_offer_text}, format="json")

        response = api_client.get(reverse("job-profile", args=[upload.data["id"]]))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["profile"]["seniority_normalized"] == "SENIOR"

    def test_experience_requirement_has_minimum_years(self, api_client, job_offer_text):
        upload = api_client.post(reverse("job-list-create"), {"text": job_offer_text}, format="json")

        response = api_client.get(reverse("job-profile", args=[upload.data["id"]]))

        requirements = response.data["profile"]["requirements"]
        experience_requirement = next(r for r in requirements if r["requirement_type"] == "EXPERIENCE")
        assert experience_requirement["minimum_years"] == 5

    def test_education_requirement_has_normalized_value(self, api_client, job_offer_text):
        upload = api_client.post(reverse("job-list-create"), {"text": job_offer_text}, format="json")

        response = api_client.get(reverse("job-profile", args=[upload.data["id"]]))

        requirements = response.data["profile"]["requirements"]
        education_requirement = next(r for r in requirements if r["requirement_type"] == "EDUCATION")
        assert education_requirement["normalized_value"] == "BACHELOR"
