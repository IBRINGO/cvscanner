"""API schemas for the Tailoring resource (Phase 5 sections 37-39).
Reads persisted Django rows directly, the same pattern as
interfaces/api/v1/analyses/serializers.py.
"""
from rest_framework import serializers

from apps.tailoring.models import TailoringChange, TailoringPlan


class TailoringChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TailoringChange
        fields = [
            "fact_id",
            "recommendation_title",
            "original_text",
            "final_text",
            "diff",
            "accepted",
            "rejection_reasons",
        ]


class TailoringPlanSummarySerializer(serializers.ModelSerializer):
    analysis_id = serializers.CharField(read_only=True)

    class Meta:
        model = TailoringPlan
        fields = [
            "id",
            "analysis_id",
            "mode",
            "engine_version",
            "status",
            "before_score",
            "after_score",
            "created_at",
            "completed_at",
        ]


class TailoringPlanDetailSerializer(serializers.ModelSerializer):
    analysis_id = serializers.CharField(read_only=True)
    changes = TailoringChangeSerializer(many=True, read_only=True)

    class Meta:
        model = TailoringPlan
        fields = [
            "id",
            "analysis_id",
            "mode",
            "engine_version",
            "status",
            "operations",
            "protected_fact_ids",
            "before_score",
            "after_score",
            "requirements_improved",
            "requirements_unchanged",
            "requirements_still_missing",
            "changes",
            "error_message",
            "created_at",
            "completed_at",
        ]


class TailoringStatusSerializer(serializers.ModelSerializer):
    error = serializers.CharField(source="error_message", read_only=True)

    class Meta:
        model = TailoringPlan
        fields = ["id", "status", "error", "completed_at"]
