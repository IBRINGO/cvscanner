"""A real embedding provider backed by Google's Gemini embedding API
(Phase 4 sections 28-31). Configured as the PRIMARY provider - see
config/container.py::build_embedding_provider for the Gemini -> OpenAI ->
none fallback chain.

Implemented with a plain HTTP call (`requests`), matching
infrastructure/embeddings/providers/openai_provider.py's approach - no
`google-generativeai` SDK dependency for what is just one POST request.
"""
import requests

from infrastructure.embeddings.base import EmbeddingProviderError

_ENDPOINT_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:batchEmbedContents"
_TIMEOUT_SECONDS = 30


class GeminiEmbeddingProvider:
    """Implements infrastructure.embeddings.base.EmbeddingProvider."""

    def __init__(self, api_key: str, model: str = "gemini-embedding-2", dimensions: int = 768) -> None:
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

        model_path = f"models/{self._model}"
        url = _ENDPOINT_TEMPLATE.format(model=self._model)
        payload = {
            "requests": [
                {"model": model_path, "content": {"parts": [{"text": text}]}} for text in texts
            ]
        }

        try:
            response = requests.post(
                url,
                params={"key": self._api_key},
                json=payload,
                timeout=_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise EmbeddingProviderError(f"Gemini embeddings request failed: {exc}") from exc

        try:
            data = response.json()
            return [item["values"] for item in data["embeddings"]]
        except (KeyError, ValueError) as exc:
            raise EmbeddingProviderError("Gemini embeddings response was malformed") from exc
