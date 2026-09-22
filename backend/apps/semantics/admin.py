from django.contrib import admin

from apps.semantics.models import SemanticRepresentation


@admin.register(SemanticRepresentation)
class SemanticRepresentationAdmin(admin.ModelAdmin):
    list_display = ("entity_type", "entity_id", "model", "version", "dimensions", "created_at")
    list_filter = ("entity_type", "model")
    search_fields = ("entity_id",)
