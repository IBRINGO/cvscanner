"""Persists an ATSAnalysis result (Phase 4 section 26).

Write-only from the domain's perspective - the API reads `Analysis`/
`RequirementEvaluationRecord` rows directly through DRF serializers
(interfaces/api/v1/analyses/serializers.py), the same pattern
interfaces/api/v1/cvs and jobs already use for CandidateProfile/
JobProfile, rather than reconstructing a domain ATSAnalysis object for
reads that nothing in the domain layer needs back.
"""
from django.utils import timezone

from apps.analyses.models import Analysis as DjangoAnalysis
from apps.analyses.models import RequirementEvaluationRecord
from domain.matching.entities import ATSAnalysis, Gap, MatchEvidence, RequirementEvaluation, ScoreBreakdown
from domain.matching.enums import AnalysisStatus


class DjangoAnalysisRepository:
    def create_pending(self, candidate_document_id: str, job_document_id: str, engine_version: str) -> str:
        row = DjangoAnalysis.objects.create(
            candidate_document_id=candidate_document_id,
            job_document_id=job_document_id,
            status=AnalysisStatus.PENDING.value,
            engine_version=engine_version,
        )
        return str(row.id)

    def get_document_pair(self, analysis_id: str) -> tuple[str, str]:
        row = DjangoAnalysis.objects.only("candidate_document_id", "job_document_id").get(id=analysis_id)
        return str(row.candidate_document_id), str(row.job_document_id)

    def mark_processing(self, analysis_id: str) -> None:
        DjangoAnalysis.objects.filter(id=analysis_id).update(status=AnalysisStatus.PROCESSING.value)

    def save_result(self, analysis_id: str, analysis: ATSAnalysis) -> None:
        row = DjangoAnalysis.objects.get(id=analysis_id)
        row.status = analysis.status.value
        row.overall_score = analysis.overall_score
        row.score_breakdown = (
            _breakdown_to_dict(analysis.score_breakdown) if analysis.score_breakdown else None
        )
        row.gaps = [_gap_to_dict(gap) for gap in analysis.gaps]
        row.metadata = analysis.metadata
        row.completed_at = timezone.now()
        row.save()

        # Idempotency (section 37): a retried task re-runs the full
        # pipeline and calls save_result again for the same analysis_id -
        # replace rather than append, exactly like the Phase 2/3 profile
        # repositories already do for reprocessing.
        RequirementEvaluationRecord.objects.filter(analysis=row).delete()
        for evaluation in analysis.requirement_evaluations:
            _create_evaluation_record(row, evaluation)

    def mark_failed(self, analysis_id: str, error_message: str) -> None:
        DjangoAnalysis.objects.filter(id=analysis_id).update(
            status=AnalysisStatus.FAILED.value,
            error_message=error_message,
            completed_at=timezone.now(),
        )


def _create_evaluation_record(row: DjangoAnalysis, evaluation: RequirementEvaluation) -> None:
    RequirementEvaluationRecord.objects.create(
        analysis=row,
        requirement_type=evaluation.requirement_type.value,
        priority=evaluation.priority.value,
        raw_text=evaluation.raw_text,
        status=evaluation.status.value,
        match_signal=evaluation.match_signal.value,
        match_strength=evaluation.match_strength.value,
        score=evaluation.score,
        confidence=evaluation.confidence,
        matched_skill=evaluation.matched_skill,
        explanation=evaluation.explanation,
        evidence=[_evidence_to_dict(item) for item in evaluation.evidence],
    )


def _evidence_to_dict(match_evidence: MatchEvidence) -> dict:
    evidence = match_evidence.evidence
    return {
        "text": evidence.text,
        "page_number": evidence.page_number,
        "section": evidence.section.value if evidence.section else None,
        "confidence": evidence.confidence,
        "extraction_method": evidence.extraction_method.value,
        "source_type": match_evidence.source_type,
        "source_label": match_evidence.source_label,
    }


def _gap_to_dict(gap: Gap) -> dict:
    return {
        "requirement_type": gap.requirement_type.value,
        "priority": gap.priority.value,
        "raw_text": gap.raw_text,
        "reason": gap.reason,
        "evidence_status": gap.evidence_status,
        "related_candidate_skills": list(gap.related_candidate_skills),
        "confidence": gap.confidence,
    }


def _breakdown_to_dict(breakdown: ScoreBreakdown) -> dict:
    return {
        "overall": breakdown.overall,
        "skills": breakdown.skills,
        "experience": breakdown.experience,
        "seniority": breakdown.seniority,
        "education": breakdown.education,
        "certifications": breakdown.certifications,
        "languages": breakdown.languages,
        "responsibilities": breakdown.responsibilities,
        "domain": breakdown.domain,
        "mandatory_gap_penalty": breakdown.mandatory_gap_penalty,
        "dimensions": [
            {
                "name": dimension.name,
                "score": dimension.score,
                "weight": dimension.weight,
                "evaluation_count": dimension.evaluation_count,
            }
            for dimension in breakdown.dimensions
        ],
    }
