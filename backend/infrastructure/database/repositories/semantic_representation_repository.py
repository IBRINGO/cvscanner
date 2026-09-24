"""Persists SemanticRepresentation rows (Phase 3 section 23). One row per
(entity_type, entity_id, model, version) - re-processing a document with
the same provider/version replaces its previous representation rather
than accumulating duplicates, mirroring the idempotency approach the
Phase 2 profile repositories already use.
"""
from apps.semantics.models import SemanticRepresentation as DjangoSemanticRepresentation
from domain.semantics.entities import SemanticRepresentation
from domain.semantics.enums import SemanticEntityType


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

    def delete_for_entity(self, entity_type: SemanticEntityType, entity_id: str) -> None:
        """SemanticRepresentation.entity_id is a loose (entity_type,
        entity_id) key, not a real foreign key (see apps/semantics/
        models.py's docstring) - so it never cascades on its own when the
        document/profile it was computed from is deleted. Callers that
        delete a document must sweep this explicitly - see
        application/documents/delete_document.py.
        """
        DjangoSemanticRepresentation.objects.filter(
            entity_type=entity_type.value, entity_id=entity_id
        ).delete()
