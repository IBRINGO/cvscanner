"""Covers config/container.py::build_embedding_provider and
build_llm_provider's selection logic directly (Phase 4 section 29,
Phase 5 sections 24/26) - which provider gets built for which
combination of configured API keys.
"""
from django.test import override_settings

from config.container import build_embedding_provider, build_llm_provider
from infrastructure.embeddings.providers.fake_provider import FakeEmbeddingProvider
from infrastructure.embeddings.providers.fallback_provider import FallbackEmbeddingProvider
from infrastructure.embeddings.providers.gemini_provider import GeminiEmbeddingProvider
from infrastructure.embeddings.providers.openai_provider import OpenAIEmbeddingProvider
from infrastructure.llm.providers.fake_provider import FakeLLMProvider
from infrastructure.llm.providers.fallback_provider import FallbackLLMProvider
from infrastructure.llm.providers.gemini_provider import GeminiLLMProvider
from infrastructure.llm.providers.openai_provider import OpenAILLMProvider


class TestBuildEmbeddingProvider:
    @override_settings(GEMINI_API_KEY="", OPENAI_API_KEY="")
    def test_no_keys_configured_returns_fake_provider(self):
        assert isinstance(build_embedding_provider(), FakeEmbeddingProvider)

    @override_settings(
        GEMINI_API_KEY="gemini-key", OPENAI_API_KEY="", GEMINI_EMBEDDING_MODEL="gemini-embedding-2"
    )
    def test_only_gemini_configured_returns_gemini_directly(self):
        provider = build_embedding_provider()
        assert isinstance(provider, GeminiEmbeddingProvider)

    @override_settings(
        GEMINI_API_KEY="", OPENAI_API_KEY="openai-key", EMBEDDING_MODEL="text-embedding-3-small"
    )
    def test_only_openai_configured_returns_openai_directly(self):
        provider = build_embedding_provider()
        assert isinstance(provider, OpenAIEmbeddingProvider)

    @override_settings(
        GEMINI_API_KEY="gemini-key",
        OPENAI_API_KEY="openai-key",
        GEMINI_EMBEDDING_MODEL="gemini-embedding-2",
        EMBEDDING_MODEL="text-embedding-3-small",
    )
    def test_both_configured_wraps_gemini_first_with_openai_fallback(self):
        provider = build_embedding_provider()
        assert isinstance(provider, FallbackEmbeddingProvider)
        assert isinstance(provider._providers[0], GeminiEmbeddingProvider)
        assert isinstance(provider._providers[1], OpenAIEmbeddingProvider)


class TestBuildLLMProvider:
    @override_settings(GEMINI_API_KEY="", OPENAI_API_KEY="")
    def test_no_keys_configured_returns_fake_provider(self):
        assert isinstance(build_llm_provider(), FakeLLMProvider)

    @override_settings(GEMINI_API_KEY="gemini-key", OPENAI_API_KEY="", GEMINI_CHAT_MODEL="gemini-2.0-flash")
    def test_only_gemini_configured_returns_gemini_directly(self):
        assert isinstance(build_llm_provider(), GeminiLLMProvider)

    @override_settings(GEMINI_API_KEY="", OPENAI_API_KEY="openai-key", OPENAI_CHAT_MODEL="gpt-4o-mini")
    def test_only_openai_configured_returns_openai_directly(self):
        assert isinstance(build_llm_provider(), OpenAILLMProvider)

    @override_settings(
        GEMINI_API_KEY="gemini-key",
        OPENAI_API_KEY="openai-key",
        GEMINI_CHAT_MODEL="gemini-2.0-flash",
        OPENAI_CHAT_MODEL="gpt-4o-mini",
    )
    def test_both_configured_wraps_gemini_first_with_openai_fallback(self):
        provider = build_llm_provider()
        assert isinstance(provider, FallbackLLMProvider)
        assert isinstance(provider._providers[0], GeminiLLMProvider)
        assert isinstance(provider._providers[1], OpenAILLMProvider)
