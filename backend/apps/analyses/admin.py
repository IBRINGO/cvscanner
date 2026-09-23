from django.contrib import admin

from apps.analyses.models import Analysis, RequirementEvaluationRecord


class RequirementEvaluationInline(admin.TabularInline):
    model = RequirementEvaluationRecord
    extra = 0
    readonly_fields = [
        "requirement_type", "priority", "raw_text", "status", "match_signal", "match_strength", "score",
    ]


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "engine_version", "overall_score", "created_at", "completed_at")
    list_filter = ("status", "engine_version")
    readonly_fields = ("id", "created_at", "completed_at")
    inlines = [RequirementEvaluationInline]
