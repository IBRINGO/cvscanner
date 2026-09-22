"""Optional embedding generation (Phase 3 sections 23-26).

Deliberately isolated from the rest of the enrichment pipeline: any
failure here (provider unreachable, malformed response, ...) is caught
and logged, never re-raised - a missing or broken embedding provider must
never take down document processing that has already produced valid
Phase 2 facts and Phase 3 normalized facts (section 62/80).

    provider needs:   name, dimensions, embed(texts: list[str])
    repository needs: save(representation) -> None
"""
import logging

from domain.semantics.entities import SemanticRepresentation
from domain.semantics.enums import SemanticEntityType
from infrastructure.embeddings.base import EmbeddingProviderError

logger = logging.getLogger(__name__)

EMBEDDING_VERSION = "1.0.0"


class GenerateSemanticEmbeddings:
    def __init__(self, provider, repository) -> None:
        self._provider = provider
        self._repository = repository

    def execute(self, entity_type: SemanticEntityType, entity_id: str, text: str) -> None:
        text = (text or "").strip()
        if not text:
            return

        try:
            vectors = self._provider.embed([text])
        except EmbeddingProviderError:
            logger.warning(
                "semantics.embedding.provider_unavailable entity_type=%s entity_id=%s",
                entity_type,
                entity_id,
            )
            return
        except Exception:
            logger.exception(
                "semantics.embedding.unexpected_error entity_type=%s entity_id=%s", entity_type, entity_id
            )
            return

        representation = SemanticRepresentation(
            entity_type=entity_type,
            entity_id=entity_id,
            text=text,
            embedding=tuple(vectors[0]),
            model=self._provider.name,
            dimensions=self._provider.dimensions,
            version=EMBEDDING_VERSION,
        )
        self._repository.save(representation)
