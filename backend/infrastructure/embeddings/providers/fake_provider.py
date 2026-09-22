"""A deterministic, dependency-free embedding provider for development
and tests (Phase 3 section 26).

This is explicitly test/dev infrastructure, not a semantic model: the
vectors it produces have no real semantic meaning - two unrelated texts
that happen to share character trigrams will look "close" under a naive
distance metric, and that is expected and fine, because nothing in Phase
3 relies on these vectors being semantically accurate. It exists purely
to exercise the EmbeddingProvider contract (shape, dimensionality,
determinism, batching) end-to-end without any network dependency or API
key, so the semantic enrichment pipeline is fully testable offline.
"""
import hashlib


class FakeEmbeddingProvider:
    """Implements infrastructure.embeddings.base.EmbeddingProvider."""

    def __init__(self, dimensions: int = 32) -> None:
        self._dimensions = dimensions

    @property
    def name(self) -> str:
        return "fake"

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        # Repeat the digest to cover `dimensions` bytes, then map each
        # byte to a float in [-1.0, 1.0] - deterministic, no external
        # calls, same text always yields the same vector.
        raw = (digest * ((self._dimensions // len(digest)) + 1))[: self._dimensions]
        return [(byte / 127.5) - 1.0 for byte in raw]
