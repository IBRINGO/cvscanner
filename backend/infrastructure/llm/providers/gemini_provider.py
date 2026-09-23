"""A real text-generation provider backed by Google's Gemini API (Phase
5 sections 24, 26). Configured as the PRIMARY provider - see
config/container.py::build_llm_provider for the Gemini -> OpenAI -> none
chain, mirroring infrastructure/embeddings' provider chain exactly.

Implemented with a plain HTTP call (`requests`), matching
infrastructure/embeddings/providers/gemini_provider.py's approach - no
`google-generativeai` SDK dependency for one POST request.
"""
import requests

from infrastructure.llm.base import LLMProviderError

_ENDPOINT_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
_TIMEOUT_SECONDS = 60


class GeminiLLMProvider:
    """Implements infrastructure.llm.base.LLMProvider."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash") -> None:
        self._api_key = api_key
        self._model = model

    @property
    def name(self) -> str:
        return self._model

    def generate(self, prompt: str) -> str:
        url = _ENDPOINT_TEMPLATE.format(model=self._model)
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        try:
            response = requests.post(
                url, params={"key": self._api_key}, json=payload, timeout=_TIMEOUT_SECONDS
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise LLMProviderError(f"Gemini generation request failed: {exc}") from exc

        try:
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, ValueError) as exc:
            raise LLMProviderError("Gemini generation response was malformed") from exc
