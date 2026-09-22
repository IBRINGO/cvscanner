"""EmbeddingProvider abstraction (Phase 3 sections 24-26).

The domain/application layers never import a concrete provider - they
depend on this Protocol's shape, and config/container.py (the
composition root) decides which implementation to build. Embeddings are
optional: a provider being unavailable or failing must degrade the
enrichment pipeline gracefully (skip embedding generation, keep
everything Phase 2 already produced), never crash the whole document
processing run - see application/semantics/generate_embeddings.py.
"""
from typing import Protocol


class EmbeddingProvider(Protocol):
    """`embed` takes a batch of texts and returns one embedding vector per
    text, in the same order. Implementations decide their own dimension
    count and must report it consistently via `dimensions`.
    """

    @property
    def name(self) -> str: ...

    @property
    def dimensions(self) -> int: ...

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class EmbeddingProviderError(Exception):
    """Raised by a provider when it cannot produce embeddings (network
    failure, missing credentials, rate limit, ...). Callers must catch
    this and degrade rather than let it propagate into document
    processing failure - see section 25/80 of the Phase 3 brief.
    """
