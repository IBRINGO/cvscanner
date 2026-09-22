"""Persistence for SemanticRepresentation (Phase 3 sections 23, 27).

Stores an embedding as a plain JSON float array rather than a pgvector
column. Phase 3 only needs a foundation for future semantic
search/matching (section 28), not similarity search at scale today -
introducing the pgvector Postgres extension now would mean a new Docker
image layer and a new migration dependency for a capability nothing yet
queries. JSON keeps this provider-agnostic and defers that real
architectural decision to whichever later phase actually needs indexed
vector search over a large corpus. See docs/adr/ for the recorded
decision.
"""
import uuid

from django.db import models

from domain.semantics.enums import SemanticEntityType


class SemanticRepresentation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity_type = models.CharField(
        max_length=32, choices=[(t.value, t.value) for t in SemanticEntityType]
    )
    entity_id = models.CharField(max_length=64)
    text = models.TextField()
    embedding = models.JSONField()
    model = models.CharField(max_length=100)
    dimensions = models.PositiveIntegerField()
    version = models.CharField(max_length=20)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["entity_type", "entity_id"])]
        constraints = [
            models.UniqueConstraint(
                fields=["entity_type", "entity_id", "model", "version"],
                name="unique_semantic_representation_per_model_version",
            )
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"SemanticRepresentation({self.entity_type}:{self.entity_id}, {self.model})"
