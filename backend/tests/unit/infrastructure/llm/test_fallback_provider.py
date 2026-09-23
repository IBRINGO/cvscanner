import pytest

from infrastructure.llm.base import LLMProviderError
from infrastructure.llm.providers.fallback_provider import FallbackLLMProvider


class _FailingProvider:
    name = "failing"

    def generate(self, prompt: str) -> str:
        raise LLMProviderError("boom")


class _WorkingProvider:
    def __init__(self, name: str, response: str) -> None:
        self.name = name
        self._response = response

    def generate(self, prompt: str) -> str:
        return self._response


class TestFallbackLLMProvider:
    def test_falls_through_to_the_next_provider_on_failure(self):
        provider = FallbackLLMProvider([_FailingProvider(), _WorkingProvider("backup", "ok")])
        assert provider.generate("prompt") == "ok"
        assert provider.name == "backup"

    def test_raises_when_every_provider_fails(self):
        provider = FallbackLLMProvider([_FailingProvider(), _FailingProvider()])
        with pytest.raises(LLMProviderError):
            provider.generate("prompt")

    def test_requires_at_least_one_provider(self):
        with pytest.raises(ValueError):
            FallbackLLMProvider([])
