"""Tries a sequence of embedding providers in order, falling through to
the next on failure (Phase 4 section 29): Gemini (primary) -> OpenAI
(fallback) -> whatever comes after. If every provider in the chain
fails, raises `EmbeddingProviderError` - the same signal a single
failing provider already gives - so callers (application/semantics/
generate_embeddings.py) need no special-casing: "no embedding could be
produced" looks identical whether there was one provider or five.

Never falls back to the domain doing something silently wrong; it only
ever changes which HTTP call was attempted last.
"""
import logging

from infrastructure.embeddings.base import EmbeddingProvider, EmbeddingProviderError

logger = logging.getLogger(__name__)


class FallbackEmbeddingProvider:
    """Implements infrastructure.embeddings.base.EmbeddingProvider."""

    def __init__(self, providers: list[EmbeddingProvider]) -> None:
        if not providers:
            raise ValueError("FallbackEmbeddingProvider requires at least one provider")
        self._providers = providers
        # Tracks whichever provider actually produced the most recent
        # embed() result, so `name`/`dimensions` (read by callers like
        # application/semantics/generate_embeddings.py right after
        # embed()) correctly attribute the result - never mislabeling an
        # OpenAI-produced vector as having come from Gemini.
        self._last_successful_provider = providers[0]

    @property
    def name(self) -> str:
        return self._last_successful_provider.name

    @property
    def dimensions(self) -> int:
        return self._last_successful_provider.dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        last_error: EmbeddingProviderError | None = None
        for provider in self._providers:
            try:
                result = provider.embed(texts)
            except EmbeddingProviderError as exc:
                logger.warning("embeddings.provider_failed provider=%s error=%s", provider.name, exc)
                last_error = exc
                continue
            self._last_successful_provider = provider
            return result
        raise last_error
