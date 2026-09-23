from django.contrib import admin

from apps.recommendations.models import Recommendation


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "priority", "confidence", "safety", "analysis", "created_at")
    list_filter = ("type", "priority", "safety")
    readonly_fields = ("id", "created_at")
