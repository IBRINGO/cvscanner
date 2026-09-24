"""Persists a TailoringPlan and its execution result (Phase 5 sections
27, 33-34). Mirrors infrastructure/database/repositories/
analysis_repository.py's shape: create a pending row synchronously (so
the API can return a plan id immediately), then a Celery task fills in
the result. `save_result` replaces (not appends) a plan's changes on
retry, the same idempotency pattern Phase 4 established for requirement
evaluations.
"""
from django.utils import timezone

from apps.analyses.models import Analysis
from apps.tailoring.models import TailoringChange as DjangoTailoringChange
from apps.tailoring.models import TailoringPlan as DjangoTailoringPlan
from domain.tailoring.entities import DiffSegment, SectionOperation, TailoredCV, TailoringPlan
from domain.tailoring.enums import TailoringMode, TailoringStatus
from domain.truth.enums import AllowedTransformation


class DjangoTailoringRepository:
    def create_pending(self, plan: TailoringPlan) -> str:
        row = DjangoTailoringPlan.objects.create(
            analysis_id=plan.analysis_id,
            mode=plan.mode.value,
            engine_version=plan.engine_version,
            status=TailoringStatus.PENDING.value,
            operations=[_operation_to_dict(op) for op in plan.operations],
            protected_fact_ids=list(plan.protected_fact_ids),
        )
        return str(row.id)

    def get_analysis_document_pair(self, analysis_id: str) -> tuple[str, str]:
        row = Analysis.objects.only("candidate_document_id", "job_document_id").get(id=analysis_id)
        return str(row.candidate_document_id), str(row.job_document_id)

    def get_plan(self, plan_id: str) -> TailoringPlan:
        row = DjangoTailoringPlan.objects.get(id=plan_id)
        return TailoringPlan(
            analysis_id=str(row.analysis_id),
            source_cv_document_id="",
            target_job_document_id="",
            mode=TailoringMode(row.mode),
            engine_version=row.engine_version,
            operations=tuple(_operation_from_dict(item) for item in row.operations),
            protected_fact_ids=tuple(row.protected_fact_ids),
        )

    def mark_status(self, plan_id: str, status: TailoringStatus) -> None:
        DjangoTailoringPlan.objects.filter(id=plan_id).update(status=status.value)

    def delete(self, plan_id: str) -> None:
        # TailoringChange rows cascade automatically (on_delete=CASCADE,
        # see apps/tailoring/models.py) - this never touches the parent
        # Analysis or the CV/job documents behind it.
        DjangoTailoringPlan.objects.filter(id=plan_id).delete()

    def mark_failed(self, plan_id: str, error_message: str) -> None:
        DjangoTailoringPlan.objects.filter(id=plan_id).update(
            status=TailoringStatus.FAILED.value, error_message=error_message, completed_at=timezone.now()
        )

    def save_result(self, plan_id: str, result: TailoredCV) -> None:
        row = DjangoTailoringPlan.objects.get(id=plan_id)
        row.status = result.status.value
        row.before_score = result.before_score
        row.after_score = result.after_score
        row.requirements_improved = result.requirements_improved
        row.requirements_unchanged = result.requirements_unchanged
        row.requirements_still_missing = result.requirements_still_missing
        row.completed_at = timezone.now()
        row.save()

        DjangoTailoringChange.objects.filter(plan=row).delete()
        for change in result.changes:
            DjangoTailoringChange.objects.create(
                plan=row,
                fact_id=change.fact_id,
                recommendation_title=change.recommendation_title,
                original_text=change.original_text,
                final_text=change.final_text,
                diff=[_diff_segment_to_dict(segment) for segment in change.diff],
                accepted=change.accepted,
                rejection_reasons=[reason.value for reason in change.rejection_reasons],
            )


def _operation_to_dict(operation: SectionOperation) -> dict:
    return {
        "fact_id": operation.fact_id,
        "transformation": operation.transformation.value,
        "recommendation_title": operation.recommendation_title,
        "target_state": operation.target_state,
    }


def _operation_from_dict(item: dict) -> SectionOperation:
    return SectionOperation(
        fact_id=item["fact_id"],
        transformation=AllowedTransformation(item["transformation"]),
        recommendation_title=item["recommendation_title"],
        target_state=item.get("target_state"),
    )


def _diff_segment_to_dict(segment: DiffSegment) -> dict:
    return {"text": segment.text, "change_type": segment.change_type.value}
