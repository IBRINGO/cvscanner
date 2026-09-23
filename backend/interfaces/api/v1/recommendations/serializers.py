"""API schema for the Recommendations resource (Phase 5 section 39).
Reads the persisted Django row directly (never exposes an internal
implementation detail beyond the row's own id) - the same read pattern
Phase 4's AnalysisDetailSerializer uses for RequirementEvaluationRecord.
"""
from rest_framework import serializers

from apps.recommendations.models import Recommendation
from domain.recommendations.enums import RecommendationSafety

_SAFE_TO_TAILOR = {RecommendationSafety.SAFE_TO_REPHRASE.value, RecommendationSafety.SAFE_TO_REORDER.value}


class RecommendationSerializer(serializers.ModelSerializer):
    related_requirement = serializers.PrimaryKeyRelatedField(read_only=True)
    safe_to_tailor = serializers.SerializerMethodField()

    class Meta:
        model = Recommendation
        fields = [
            "id",
            "type",
            "priority",
            "confidence",
            "safety",
            "impact",
            "title",
            "summary",
            "reason",
            "suggested_action",
            "related_requirement",
            "supporting_evidence",
            "current_state",
            "target_state",
            "safe_to_tailor",
            "created_at",
        ]

    def get_safe_to_tailor(self, recommendation: Recommendation) -> bool:
        return recommendation.safety in _SAFE_TO_TAILOR
