import pytest
from django.urls import reverse
from rest_framework import status

from apps.tailoring.models import TailoringChange, TailoringPlan


@pytest.mark.django_db
class TestTailoringDelete:
    def test_deletes_a_completed_plan(self, api_client, completed_analysis_id, safe_recommendation_ids):
        create = api_client.post(
            reverse("tailoring-list-create"),
            {
                "analysis_id": completed_analysis_id,
                "mode": "CONSERVATIVE",
                "recommendation_ids": safe_recommendation_ids,
            },
            format="json",
        )
        plan_id = create.data["id"]

        response = api_client.delete(reverse("tailoring-detail", args=[plan_id]))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not TailoringPlan.objects.filter(id=plan_id).exists()

    def test_deleting_a_plan_removes_its_changes_too(
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
        plan_id = create.data["id"]
        assert TailoringChange.objects.filter(plan_id=plan_id).exists()

        api_client.delete(reverse("tailoring-detail", args=[plan_id]))

        assert not TailoringChange.objects.filter(plan_id=plan_id).exists()

    def test_deleting_a_plan_does_not_touch_its_analysis(
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
        plan_id = create.data["id"]

        api_client.delete(reverse("tailoring-detail", args=[plan_id]))

        analysis_response = api_client.get(reverse("analysis-detail", args=[completed_analysis_id]))
        assert analysis_response.status_code == status.HTTP_200_OK

    def test_deleted_plan_no_longer_appears_in_the_list(
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
        plan_id = create.data["id"]
        api_client.delete(reverse("tailoring-detail", args=[plan_id]))

        response = api_client.get(reverse("tailoring-list-create"))

        assert all(plan["id"] != plan_id for plan in response.data)

    def test_deleting_an_unknown_plan_returns_404(self, api_client):
        response = api_client.delete(
            reverse("tailoring-detail", args=["00000000-0000-0000-0000-000000000000"])
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
