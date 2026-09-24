"""Proves that deleting a CV or job-offer document actually removes
every dependent row (CandidateProfile/JobProfile and their children,
Analysis, Recommendation, TailoringPlan/TailoringChange, Evidence,
SemanticRepresentation) rather than just the Document row - see
application/documents/delete_document.py. Lives alongside the tailoring
tests specifically to reuse their conftest (a real CV+job+analysis+
recommendations+tailoring-plan chain, with the deterministic embedding
stub so recommendation generation is not flaky).
"""
import pytest
from django.urls import reverse
from rest_framework import status

from apps.analyses.models import Analysis
from apps.candidates.models import CandidateProfile
from apps.documents.models import Evidence
from apps.jobs.models import JobProfile
from apps.recommendations.models import Recommendation
from apps.semantics.models import SemanticRepresentation
from apps.tailoring.models import TailoringChange, TailoringPlan


@pytest.fixture
def full_chain(api_client, processed_cv_id, processed_job_id, completed_analysis_id, safe_recommendation_ids):
    # Recommendations are generated lazily on first read (see
    # interfaces/api/v1/recommendations/views.py) - fetch them so the
    # rows this test asserts on actually exist before deletion.
    api_client.get(reverse("analysis-recommendations", args=[completed_analysis_id]))

    plan_response = api_client.post(
        reverse("tailoring-list-create"),
        {
            "analysis_id": completed_analysis_id,
            "mode": "CONSERVATIVE",
            "recommendation_ids": safe_recommendation_ids,
        },
        format="json",
    )
    return {
        "cv_id": processed_cv_id,
        "job_id": processed_job_id,
        "analysis_id": completed_analysis_id,
        "plan_id": plan_response.data["id"],
    }


@pytest.mark.django_db
class TestDeletingACvCascades:
    def test_the_full_chain_exists_before_deletion(self, full_chain):
        assert CandidateProfile.objects.filter(document_id=full_chain["cv_id"]).exists()
        assert Analysis.objects.filter(id=full_chain["analysis_id"]).exists()
        assert Recommendation.objects.filter(analysis_id=full_chain["analysis_id"]).exists()
        assert TailoringPlan.objects.filter(id=full_chain["plan_id"]).exists()
        assert TailoringChange.objects.filter(plan_id=full_chain["plan_id"]).exists()
        assert Evidence.objects.filter(source_document_id=full_chain["cv_id"]).exists()
        assert SemanticRepresentation.objects.filter(
            entity_type="CANDIDATE_PROFILE", entity_id=full_chain["cv_id"]
        ).exists()

    def test_deleting_the_cv_removes_its_own_profile_and_evidence(self, api_client, full_chain):
        api_client.delete(reverse("cv-detail", args=[full_chain["cv_id"]]))

        assert not CandidateProfile.objects.filter(document_id=full_chain["cv_id"]).exists()
        assert not Evidence.objects.filter(source_document_id=full_chain["cv_id"]).exists()
        assert not SemanticRepresentation.objects.filter(
            entity_type="CANDIDATE_PROFILE", entity_id=full_chain["cv_id"]
        ).exists()

    def test_deleting_the_cv_removes_the_analysis_built_from_it(self, api_client, full_chain):
        api_client.delete(reverse("cv-detail", args=[full_chain["cv_id"]]))

        assert not Analysis.objects.filter(id=full_chain["analysis_id"]).exists()

    def test_deleting_the_cv_removes_recommendations_and_the_tailoring_plan(self, api_client, full_chain):
        api_client.delete(reverse("cv-detail", args=[full_chain["cv_id"]]))

        assert not Recommendation.objects.filter(analysis_id=full_chain["analysis_id"]).exists()
        assert not TailoringPlan.objects.filter(id=full_chain["plan_id"]).exists()
        assert not TailoringChange.objects.filter(plan_id=full_chain["plan_id"]).exists()

    def test_deleting_the_cv_never_touches_the_job_offer_side(self, api_client, full_chain):
        api_client.delete(reverse("cv-detail", args=[full_chain["cv_id"]]))

        job_response = api_client.get(reverse("job-detail", args=[full_chain["job_id"]]))
        assert job_response.status_code == status.HTTP_200_OK
        assert JobProfile.objects.filter(document_id=full_chain["job_id"]).exists()


@pytest.mark.django_db
class TestDeletingAJobOfferCascades:
    def test_deleting_the_job_removes_the_analysis_and_everything_after_it(self, api_client, full_chain):
        api_client.delete(reverse("job-detail", args=[full_chain["job_id"]]))

        assert not Analysis.objects.filter(id=full_chain["analysis_id"]).exists()
        assert not Recommendation.objects.filter(analysis_id=full_chain["analysis_id"]).exists()
        assert not TailoringPlan.objects.filter(id=full_chain["plan_id"]).exists()
        assert not JobProfile.objects.filter(document_id=full_chain["job_id"]).exists()
        assert not SemanticRepresentation.objects.filter(
            entity_type="JOB_PROFILE", entity_id=full_chain["job_id"]
        ).exists()

    def test_deleting_the_job_offer_never_touches_the_cv_side(self, api_client, full_chain):
        api_client.delete(reverse("job-detail", args=[full_chain["job_id"]]))

        cv_response = api_client.get(reverse("cv-detail", args=[full_chain["cv_id"]]))
        assert cv_response.status_code == status.HTTP_200_OK
        assert CandidateProfile.objects.filter(document_id=full_chain["cv_id"]).exists()
