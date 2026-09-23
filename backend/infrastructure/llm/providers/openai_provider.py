"""A real text-generation provider backed by OpenAI's chat completions
REST endpoint (Phase 5 sections 24, 26). Configured as the FALLBACK
provider - see config/container.py::build_llm_provider.

Plain HTTP call (`requests`), matching
infrastructure/embeddings/providers/openai_provider.py's approach - no
SDK dependency for one POST request.
"""
import requests

from infrastructure.llm.base import LLMProviderError

_ENDPOINT = "https://api.openai.com/v1/chat/completions"
_TIMEOUT_SECONDS = 60


class OpenAILLMProvider:
    """Implements infrastructure.llm.base.LLMProvider."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self._api_key = api_key
        self._model = model

    @property
    def name(self) -> str:
        return self._model

    def generate(self, prompt: str) -> str:
        try:
            response = requests.post(
                _ENDPOINT,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise LLMProviderError(f"OpenAI generation request failed: {exc}") from exc

        try:
            payload = response.json()
            return payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as exc:
            raise LLMProviderError("OpenAI generation response was malformed") from exc
