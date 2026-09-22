"""Persists SemanticRepresentation rows (Phase 3 section 23). One row per
(entity_type, entity_id, model, version) - re-processing a document with
the same provider/version replaces its previous representation rather
than accumulating duplicates, mirroring the idempotency approach the
Phase 2 profile repositories already use.
"""
from apps.semantics.models import SemanticRepresentation as DjangoSemanticRepresentation
from domain.semantics.entities import SemanticRepresentation


class DjangoSemanticRepresentationRepository:
    def save(self, representation: SemanticRepresentation) -> None:
        DjangoSemanticRepresentation.objects.update_or_create(
            entity_type=representation.entity_type.value,
            entity_id=representation.entity_id,
            model=representation.model,
            version=representation.version,
            defaults={
                "text": representation.text,
                "embedding": list(representation.embedding),
                "dimensions": representation.dimensions,
                "metadata": representation.metadata,
            },
        )
