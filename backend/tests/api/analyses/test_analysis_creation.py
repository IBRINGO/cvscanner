"""End-to-end API tests for analysis creation (Phase 4 sections 34-37).
Uses the real sample CV/job fixtures already processed through the real
Phase 2 pipeline (CELERY_TASK_ALWAYS_EAGER makes this synchronous in
tests) - the same fixtures document a shared company/overlapping tech
stack (see tests/fixtures/generate_fixtures.py), so a real hybrid match
is exercised end to end, not a hand-built domain object.
"""
import pytest
from django.urls import reverse
from rest_framework import status

from apps.analyses.models import Analysis


@pytest.mark.django_db
class TestAnalysisCreation:
    def test_creates_and_completes_an_analysis(self, api_client, processed_cv_id, processed_job_id):
        response = api_client.post(
            reverse("analysis-list-create"),
            {"candidate_document_id": processed_cv_id, "job_document_id": processed_job_id},
            format="json",
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        analysis_id = response.data["id"]

        detail = api_client.get(reverse("analysis-detail", args=[analysis_id]))
        assert detail.status_code == status.HTTP_200_OK
        assert detail.data["status"] == "COMPLETED"
        assert detail.data["overall_score"] is not None
        assert detail.data["engine_version"]

    def test_matches_the_shared_python_django_postgresql_requirements(
        self, api_client, processed_cv_id, processed_job_id
    ):
        create = api_client.post(
            reverse("analysis-list-create"),
            {"candidate_document_id": processed_cv_id, "job_document_id": processed_job_id},
            format="json",
        )
        detail = api_client.get(reverse("analysis-detail", args=[create.data["id"]]))

        evaluations = {e["raw_text"]: e for e in detail.data["requirement_evaluations"]}
        assert evaluations["Python"]["match_signal"] == "EXACT_MATCH"
        assert evaluations["Django"]["match_signal"] == "EXACT_MATCH"
        assert evaluations["PostgreSQL"]["match_signal"] == "EXACT_MATCH"

    def test_response_never_contains_a_generic_compatibility_percentage_label(
        self, api_client, processed_cv_id, processed_job_id
    ):
        # Phase 4 still must not present itself as a candidate ranking or
        # a bare score with no explanation (section 79) - this is a
        # negative check on the raw response text for banned wording.
        create = api_client.post(
            reverse("analysis-list-create"),
            {"candidate_document_id": processed_cv_id, "job_document_id": processed_job_id},
            format="json",
        )
        detail = api_client.get(reverse("analysis-detail", args=[create.data["id"]]))

        body = str(detail.data).lower()
        assert "ats_score" not in body
        assert "ranking" not in body

    def test_missing_ids_are_rejected(self, api_client):
        response = api_client.post(reverse("analysis-list-create"), {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_nonexistent_document_ids_return_404(self, api_client):
        import uuid

        response = api_client.post(
            reverse("analysis-list-create"),
            {"candidate_document_id": str(uuid.uuid4()), "job_document_id": str(uuid.uuid4())},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unprocessed_document_is_rejected(self, api_client, processed_job_id):
        from apps.documents.models import Document

        pending_cv = Document.objects.create(
            document_type="CV",
            original_filename="cv.pdf",
            mime_type="application/pdf",
            file_size=10,
            file_hash="z" * 64,
            storage_reference="cv/z.pdf",
            status="UPLOADED",
        )

        response = api_client.post(
            reverse("analysis-list-create"),
            {"candidate_document_id": str(pending_cv.id), "job_document_id": processed_job_id},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_analysis_status_endpoint(self, api_client, processed_cv_id, processed_job_id):
        create = api_client.post(
            reverse("analysis-list-create"),
            {"candidate_document_id": processed_cv_id, "job_document_id": processed_job_id},
            format="json",
        )

        response = api_client.get(reverse("analysis-status", args=[create.data["id"]]))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "COMPLETED"

    def test_analysis_list_endpoint(self, api_client, processed_cv_id, processed_job_id):
        api_client.post(
            reverse("analysis-list-create"),
            {"candidate_document_id": processed_cv_id, "job_document_id": processed_job_id},
            format="json",
        )

        response = api_client.get(reverse("analysis-list-create"))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_retrying_does_not_duplicate_requirement_evaluations(
        self, api_client, processed_cv_id, processed_job_id
    ):
        from config.container import build_run_analysis

        create = api_client.post(
            reverse("analysis-list-create"),
            {"candidate_document_id": processed_cv_id, "job_document_id": processed_job_id},
            format="json",
        )
        analysis_id = create.data["id"]
        before_count = Analysis.objects.get(id=analysis_id).requirement_evaluations.count()

        build_run_analysis().execute(analysis_id)  # simulate a Celery retry

        after_count = Analysis.objects.get(id=analysis_id).requirement_evaluations.count()
        assert after_count == before_count
