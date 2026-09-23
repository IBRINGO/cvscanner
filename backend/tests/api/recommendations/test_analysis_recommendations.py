"""End-to-end API tests for the recommendations endpoint (Phase 5
sections 6-13, 37). Uses the real sample CV/job fixtures already
processed and analyzed through the real Phase 2/4 pipelines
(CELERY_TASK_ALWAYS_EAGER makes this synchronous in tests) - a real
hybrid analysis with a genuine Kubernetes/AWS gap is exercised end to
end.
"""
import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestAnalysisRecommendations:
    def test_returns_recommendations_for_a_completed_analysis(self, api_client, completed_analysis_id):
        response = api_client.get(reverse("analysis-recommendations", args=[completed_analysis_id]))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0
        first = response.data[0]
        assert set(first.keys()) >= {
            "id", "type", "priority", "confidence", "safety", "impact",
            "title", "summary", "reason", "suggested_action", "safe_to_tailor",
        }

    def test_a_missing_kubernetes_requirement_produces_a_not_safe_recommendation(
        self, api_client, completed_analysis_id
    ):
        response = api_client.get(reverse("analysis-recommendations", args=[completed_analysis_id]))

        titles = {r["title"]: r for r in response.data}
        kubernetes_recs = [r for title, r in titles.items() if "Kubernetes" in title]
        assert kubernetes_recs
        assert kubernetes_recs[0]["safe_to_tailor"] is False

    def test_calling_twice_does_not_duplicate_recommendations(self, api_client, completed_analysis_id):
        first = api_client.get(reverse("analysis-recommendations", args=[completed_analysis_id]))
        second = api_client.get(reverse("analysis-recommendations", args=[completed_analysis_id]))

        assert len(first.data) == len(second.data)

    def test_returns_404_for_an_unknown_analysis(self, api_client):
        import uuid

        response = api_client.get(reverse("analysis-recommendations", args=[uuid.uuid4()]))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_never_exposes_a_raw_score_optimization_framing(self, api_client, completed_analysis_id):
        response = api_client.get(reverse("analysis-recommendations", args=[completed_analysis_id]))
        body = str(response.data).lower()
        assert "guaranteed" not in body
        assert "score increase" not in body
