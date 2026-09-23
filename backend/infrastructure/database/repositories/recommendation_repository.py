"""Persists and retrieves Recommendation rows (Phase 5 section 34).

Write-once per (analysis, engine_version): recommendations are cheap and
deterministic to compute (no LLM/embedding calls - see
domain/recommendations/engine.py), so this repository's `get_or_create`
either returns an already-persisted set or computes and saves a fresh
one, rather than needing an async Celery workflow the way the more
expensive analysis/tailoring runs do.
"""
from apps.analyses.models import RequirementEvaluationRecord
from apps.recommendations.models import Recommendation as DjangoRecommendation
from domain.matching.entities import MatchEvidence
from domain.recommendations.entities import Recommendation
from domain.recommendations.enums import (
    RecommendationConfidence,
    RecommendationImpact,
    RecommendationPriority,
    RecommendationSafety,
    RecommendationType,
)


class DjangoRecommendationRepository:
    def get_for_analysis(self, analysis_id: str, engine_version: str) -> tuple[Recommendation, ...] | None:
        rows = DjangoRecommendation.objects.filter(
            analysis_id=analysis_id, engine_version=engine_version
        ).order_by("id")
        if not rows.exists():
            return None
        return tuple(_recommendation_from_row(row) for row in rows)

    def get_selected(self, analysis_id: str, recommendation_ids: list[str]) -> tuple[Recommendation, ...]:
        """Recommendation ids are the persisted row's own UUID - the
        domain `Recommendation` dataclass carries no id of its own (it is
        recomputed fresh each engine run, per
        domain/recommendations/entities.py), so selection by id always
        goes through the Django row, the same read pattern Phase 4 uses
        for Analysis/RequirementEvaluationRecord.
        """
        rows = DjangoRecommendation.objects.filter(analysis_id=analysis_id, id__in=recommendation_ids)
        return tuple(_recommendation_from_row(row) for row in rows)

    def save(
        self, analysis_id: str, engine_version: str, recommendations: tuple[Recommendation, ...]
    ) -> None:
        evaluation_ids = list(
            RequirementEvaluationRecord.objects.filter(analysis_id=analysis_id)
            .order_by("id")
            .values_list("id", flat=True)
        )
        DjangoRecommendation.objects.filter(analysis_id=analysis_id, engine_version=engine_version).delete()
        for recommendation in recommendations:
            related_requirement_id = (
                evaluation_ids[recommendation.related_requirement_index]
                if recommendation.related_requirement_index is not None
                and recommendation.related_requirement_index < len(evaluation_ids)
                else None
            )
            DjangoRecommendation.objects.create(
                analysis_id=analysis_id,
                engine_version=engine_version,
                type=recommendation.type.value,
                priority=recommendation.priority.value,
                confidence=recommendation.confidence.value,
                safety=recommendation.safety.value,
                impact=recommendation.impact.value,
                title=recommendation.title,
                summary=recommendation.summary,
                reason=recommendation.reason,
                suggested_action=recommendation.suggested_action,
                related_requirement_id=related_requirement_id,
                supporting_evidence=[_evidence_to_dict(item) for item in recommendation.supporting_evidence],
                current_state=recommendation.current_state,
                target_state=recommendation.target_state,
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


def _recommendation_from_row(row: DjangoRecommendation) -> Recommendation:
    return Recommendation(
        type=RecommendationType(row.type),
        priority=RecommendationPriority(row.priority),
        confidence=RecommendationConfidence(row.confidence),
        safety=RecommendationSafety(row.safety),
        impact=RecommendationImpact(row.impact),
        title=row.title,
        summary=row.summary,
        reason=row.reason,
        suggested_action=row.suggested_action,
        related_requirement_index=None,
        current_state=row.current_state,
        target_state=row.target_state,
    )
