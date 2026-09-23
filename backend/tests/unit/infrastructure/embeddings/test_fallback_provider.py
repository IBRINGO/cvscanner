import pytest

from infrastructure.embeddings.base import EmbeddingProviderError
from infrastructure.embeddings.providers.fallback_provider import FallbackEmbeddingProvider


class FakeProvider:
    def __init__(self, name: str, dimensions: int = 4, error: Exception | None = None):
        self._name = name
        self._dimensions = dimensions
        self._error = error
        self.called = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed(self, texts):
        self.called = True
        if self._error:
            raise self._error
        return [[1.0] * self._dimensions for _ in texts]


class TestFallbackEmbeddingProvider:
    def test_uses_the_first_provider_when_it_succeeds(self):
        primary = FakeProvider("gemini")
        secondary = FakeProvider("openai")
        provider = FallbackEmbeddingProvider([primary, secondary])

        provider.embed(["hello"])

        assert primary.called
        assert not secondary.called
        assert provider.name == "gemini"

    def test_falls_back_to_the_second_provider_on_failure(self):
        primary = FakeProvider("gemini", error=EmbeddingProviderError("down"))
        secondary = FakeProvider("openai")
        provider = FallbackEmbeddingProvider([primary, secondary])

        vectors = provider.embed(["hello"])

        assert secondary.called
        assert provider.name == "openai"
        assert len(vectors[0]) == secondary.dimensions

    def test_name_and_dimensions_reflect_whichever_provider_actually_succeeded(self):
        primary = FakeProvider("gemini", dimensions=768, error=EmbeddingProviderError("down"))
        secondary = FakeProvider("openai", dimensions=1536)
        provider = FallbackEmbeddingProvider([primary, secondary])

        provider.embed(["hello"])

        assert provider.dimensions == 1536

    def test_raises_when_every_provider_fails(self):
        primary = FakeProvider("gemini", error=EmbeddingProviderError("down"))
        secondary = FakeProvider("openai", error=EmbeddingProviderError("also down"))
        provider = FallbackEmbeddingProvider([primary, secondary])

        with pytest.raises(EmbeddingProviderError):
            provider.embed(["hello"])

    def test_requires_at_least_one_provider(self):
        with pytest.raises(ValueError):
            FallbackEmbeddingProvider([])
