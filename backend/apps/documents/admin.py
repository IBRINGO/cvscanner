from django.contrib import admin

from apps.documents.models import Document, Evidence


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "document_type", "original_filename", "status", "created_at")
    list_filter = ("document_type", "status")
    search_fields = ("original_filename", "file_hash")
    readonly_fields = ("file_hash", "storage_reference", "created_at", "updated_at")


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ("id", "source_document", "section", "extraction_method", "confidence")
    list_filter = ("section", "extraction_method")
