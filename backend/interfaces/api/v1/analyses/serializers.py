"""API schemas for the Analyses resource (Phase 4 section 35). Never
exposes a raw database id beyond the Analysis/requirement-evaluation
row's own UUID/PK (needed for routing) - no internal implementation
detail (e.g. which repository/table shape produced a value) leaks
through.
"""
from rest_framework import serializers

from apps.analyses.models import Analysis, RequirementEvaluationRecord


class RequirementEvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequirementEvaluationRecord
        fields = [
            "requirement_type",
            "priority",
            "raw_text",
            "status",
            "match_signal",
            "match_strength",
            "score",
            "confidence",
            "matched_skill",
            "explanation",
            "evidence",
        ]


class AnalysisSummarySerializer(serializers.ModelSerializer):
    candidate_document_id = serializers.CharField(read_only=True)
    job_document_id = serializers.CharField(read_only=True)

    class Meta:
        model = Analysis
        fields = [
            "id",
            "candidate_document_id",
            "job_document_id",
            "status",
            "engine_version",
            "overall_score",
            "created_at",
            "completed_at",
        ]


class AnalysisDetailSerializer(serializers.ModelSerializer):
    candidate_document_id = serializers.CharField(read_only=True)
    job_document_id = serializers.CharField(read_only=True)
    requirement_evaluations = RequirementEvaluationSerializer(many=True, read_only=True)
    requirement_summary = serializers.SerializerMethodField()

    class Meta:
        model = Analysis
        fields = [
            "id",
            "candidate_document_id",
            "job_document_id",
            "status",
            "engine_version",
            "overall_score",
            "score_breakdown",
            "requirement_summary",
            "requirement_evaluations",
            "gaps",
            "error_message",
            "created_at",
            "completed_at",
        ]

    def get_requirement_summary(self, analysis: Analysis) -> dict:
        evaluations = list(analysis.requirement_evaluations.all())
        return {
            "total": len(evaluations),
            "met": sum(1 for e in evaluations if e.status == "MET"),
            "partially_met": sum(1 for e in evaluations if e.status == "PARTIALLY_MET"),
            "not_met": sum(1 for e in evaluations if e.status == "NOT_MET"),
            "unknown": sum(1 for e in evaluations if e.status == "UNKNOWN"),
        }


class AnalysisStatusSerializer(serializers.ModelSerializer):
    error = serializers.CharField(source="error_message", read_only=True)

    class Meta:
        model = Analysis
        fields = ["id", "status", "error", "completed_at"]
