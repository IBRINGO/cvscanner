from django.contrib import admin

from apps.tailoring.models import TailoringChange, TailoringPlan


class TailoringChangeInline(admin.TabularInline):
    model = TailoringChange
    extra = 0
    readonly_fields = ["fact_id", "recommendation_title", "accepted"]


@admin.register(TailoringPlan)
class TailoringPlanAdmin(admin.ModelAdmin):
    list_display = ("id", "mode", "status", "before_score", "after_score", "analysis", "created_at")
    list_filter = ("mode", "status")
    readonly_fields = ("id", "created_at", "completed_at")
    inlines = [TailoringChangeInline]
