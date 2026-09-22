"""A real embedding provider backed by OpenAI's embeddings REST endpoint.

Deliberately implemented with a plain HTTP call (`requests`) rather than
the `openai` SDK - the only thing this needs is one POST request, and
avoiding the SDK keeps this dependency small and easy to audit. Never
imported by domain/ or application/ directly; config/container.py decides
whether to build this or infrastructure.embeddings.providers.fake_provider
.FakeEmbeddingProvider, based on whether an API key is configured -
embeddings are optional (Phase 3 section 25), so the absence of a key is
never treated as an error at import time.
"""
import requests

from infrastructure.embeddings.base import EmbeddingProviderError

_ENDPOINT = "https://api.openai.com/v1/embeddings"
_TIMEOUT_SECONDS = 30


class OpenAIEmbeddingProvider:
    """Implements infrastructure.embeddings.base.EmbeddingProvider."""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small", dimensions: int = 1536) -> None:
        self._api_key = api_key
        self._model = model
        self._dimensions = dimensions

    @property
    def name(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = requests.post(
                _ENDPOINT,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"model": self._model, "input": texts},
                timeout=_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise EmbeddingProviderError(f"OpenAI embeddings request failed: {exc}") from exc

        try:
            payload = response.json()
            return [item["embedding"] for item in payload["data"]]
        except (KeyError, ValueError) as exc:
            raise EmbeddingProviderError("OpenAI embeddings response was malformed") from exc
