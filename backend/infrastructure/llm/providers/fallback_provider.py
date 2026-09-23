"""Tries a sequence of LLM providers in order, falling through to the
next on failure - mirrors
infrastructure/embeddings/providers/fallback_provider.py exactly
(Gemini primary, OpenAI fallback). If every provider fails, raises
`LLMProviderError`; callers degrade by keeping the original text for
whatever section was being generated, never by failing the whole
tailoring run (see infrastructure/llm/base.py).
"""
import logging

from infrastructure.llm.base import LLMProvider, LLMProviderError

logger = logging.getLogger(__name__)


class FallbackLLMProvider:
    """Implements infrastructure.llm.base.LLMProvider."""

    def __init__(self, providers: list[LLMProvider]) -> None:
        if not providers:
            raise ValueError("FallbackLLMProvider requires at least one provider")
        self._providers = providers
        self._last_successful_provider = providers[0]

    @property
    def name(self) -> str:
        return self._last_successful_provider.name

    def generate(self, prompt: str) -> str:
        last_error: LLMProviderError | None = None
        for provider in self._providers:
            try:
                result = provider.generate(prompt)
            except LLMProviderError as exc:
                logger.warning("llm.provider_failed provider=%s error=%s", provider.name, exc)
                last_error = exc
                continue
            self._last_successful_provider = provider
            return result
        raise last_error
