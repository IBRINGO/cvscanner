"""Persistence models for the documents app.

Document ingestion/processing state and evidence records. These are
infrastructure/persistence concerns - the business rules about what a
Document is and how its status may change live in domain/documents/
(framework-free). See docs/architecture/dependency-rule.md.

Phase 2 access note: there is no authentication yet (see Phase 1's known
limitations, still true here). `owner` is nullable and nothing in
interfaces/api scopes documents to a request's user. Any document's UUID
is enough to read its status/profile - this is a deliberate, documented
temporary assumption for local development, not a production access
model. See docs/architecture/phase-2-pipeline.md "Security baseline".
"""
import uuid

from django.conf import settings
from django.db import models

from domain.documents.enums import DocumentType, ExtractionMethod, ProcessingStatus, SectionType


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="documents"
    )
    document_type = models.CharField(
        max_length=16, choices=[(t.value, t.value) for t in DocumentType]
    )
    original_filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=127)
    file_size = models.PositiveIntegerField()
    file_hash = models.CharField(max_length=64, db_index=True)  # sha256 hex digest
    storage_reference = models.CharField(max_length=512)
    status = models.CharField(
        max_length=16,
        choices=[(s.value, s.value) for s in ProcessingStatus],
        default=ProcessingStatus.UPLOADED.value,
    )
    page_count = models.PositiveIntegerField(null=True, blank=True)
    extracted_text = models.TextField(null=True, blank=True)
    sections = models.JSONField(null=True, blank=True)
    processing_metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["file_hash", "document_type"]),
            models.Index(fields=["status"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - debug convenience only
        return f"{self.document_type} {self.id} ({self.status})"


class Evidence(models.Model):
    """Provenance for one extracted fact. See domain/documents/evidence.py
    for what `confidence` does and does not mean.
    """

    source_document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="evidence_records")
    page_number = models.PositiveIntegerField(null=True, blank=True)
    section = models.CharField(
        max_length=32, choices=[(s.value, s.value) for s in SectionType], null=True, blank=True
    )
    text = models.TextField()
    start_offset = models.PositiveIntegerField(null=True, blank=True)
    end_offset = models.PositiveIntegerField(null=True, blank=True)
    confidence = models.FloatField()
    extraction_method = models.CharField(
        max_length=16, choices=[(m.value, m.value) for m in ExtractionMethod]
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "evidence records"

    def __str__(self) -> str:  # pragma: no cover
        return f"Evidence({self.text[:40]!r})"
