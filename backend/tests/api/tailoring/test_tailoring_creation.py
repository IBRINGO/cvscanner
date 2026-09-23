"""End-to-end API tests for the tailoring workflow (Phase 5 sections
27-39, 73, 83). Uses the real sample CV/job fixtures already processed
and analyzed through the real Phase 2/4 pipelines
(CELERY_TASK_ALWAYS_EAGER makes this synchronous in tests) - a real
tailoring plan, generation, Truth Layer validation, and Phase 4
re-analysis run end to end against real data.
"""
import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestTailoringCreation:
    def test_creates_and_completes_a_conservative_tailoring_run(
        self, api_client, completed_analysis_id, safe_recommendation_ids
    ):
        assert safe_recommendation_ids, "fixture data must produce at least one safe recommendation"

        create = api_client.post(
            reverse("tailoring-list-create"),
            {
                "analysis_id": completed_analysis_id,
                "mode": "CONSERVATIVE",
                "recommendation_ids": safe_recommendation_ids,
            },
            format="json",
        )
        assert create.status_code == status.HTTP_202_ACCEPTED
        plan_id = create.data["id"]

        detail = api_client.get(reverse("tailoring-detail", args=[plan_id]))
        assert detail.status_code == status.HTTP_200_OK
        assert detail.data["status"] == "COMPLETED"
        assert detail.data["before_score"] is not None
        assert detail.data["after_score"] is not None
        # Multiple recommendations can legitimately target the same
        # underlying fact (e.g. several responsibilities all pointing at
        # one experience bullet) - the planner deduplicates by fact_id,
        # so the change count is at most, not exactly, the selection count.
        assert 1 <= len(detail.data["changes"]) <= len(safe_recommendation_ids)

    def test_no_change_ever_introduces_an_unsupported_technology(
        self, api_client, completed_analysis_id, safe_recommendation_ids
    ):
        create = api_client.post(
            reverse("tailoring-list-create"),
            {
                "analysis_id": completed_analysis_id,
                "mode": "AGGRESSIVE_SAFE",
                "recommendation_ids": safe_recommendation_ids,
            },
            format="json",
        )
        detail = api_client.get(reverse("tailoring-detail", args=[create.data["id"]]))

        for change in detail.data["changes"]:
            if change["accepted"]:
                assert "UNSUPPORTED_TECHNOLOGY" not in change["rejection_reasons"]

    def test_status_endpoint_reflects_completion(
        self, api_client, completed_analysis_id, safe_recommendation_ids
    ):
        create = api_client.post(
            reverse("tailoring-list-create"),
            {
                "analysis_id": completed_analysis_id,
                "mode": "CONSERVATIVE",
                "recommendation_ids": safe_recommendation_ids,
            },
            format="json",
        )
        response = api_client.get(reverse("tailoring-status", args=[create.data["id"]]))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "COMPLETED"

    def test_changes_endpoint_returns_the_diff(
        self, api_client, completed_analysis_id, safe_recommendation_ids
    ):
        create = api_client.post(
            reverse("tailoring-list-create"),
            {
                "analysis_id": completed_analysis_id,
                "mode": "CONSERVATIVE",
                "recommendation_ids": safe_recommendation_ids,
            },
            format="json",
        )
        response = api_client.get(reverse("tailoring-changes", args=[create.data["id"]]))
        assert response.status_code == status.HTTP_200_OK
        assert 1 <= len(response.data) <= len(safe_recommendation_ids)
        assert "diff" in response.data[0]

    def test_rejects_when_analysis_is_not_completed(self, api_client, processed_cv_id, processed_job_id):
        from apps.analyses.models import Analysis

        pending = Analysis.objects.create(
            candidate_document_id=processed_cv_id,
            job_document_id=processed_job_id,
            status="PENDING",
            engine_version="1.0.0",
        )
        response = api_client.post(
            reverse("tailoring-list-create"),
            {"analysis_id": str(pending.id), "mode": "CONSERVATIVE", "recommendation_ids": ["x"]},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_rejects_an_unsafe_recommendation_selection(self, api_client, completed_analysis_id):
        recs = api_client.get(reverse("analysis-recommendations", args=[completed_analysis_id]))
        unsafe_ids = [r["id"] for r in recs.data if not r["safe_to_tailor"]]
        assert unsafe_ids, "fixture data must produce at least one not-safe recommendation"

        response = api_client.post(
            reverse("tailoring-list-create"),
            {"analysis_id": completed_analysis_id, "mode": "CONSERVATIVE", "recommendation_ids": unsafe_ids},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_fields_are_rejected(self, api_client):
        response = api_client.post(reverse("tailoring-list-create"), {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_mode_is_rejected(self, api_client, completed_analysis_id, safe_recommendation_ids):
        response = api_client.post(
            reverse("tailoring-list-create"),
            {
                "analysis_id": completed_analysis_id,
                "mode": "NOT_A_REAL_MODE",
                "recommendation_ids": safe_recommendation_ids,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_endpoint_returns_created_plans(
        self, api_client, completed_analysis_id, safe_recommendation_ids
    ):
        api_client.post(
            reverse("tailoring-list-create"),
            {
                "analysis_id": completed_analysis_id,
                "mode": "CONSERVATIVE",
                "recommendation_ids": safe_recommendation_ids,
            },
            format="json",
        )
        response = api_client.get(reverse("tailoring-list-create"))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
