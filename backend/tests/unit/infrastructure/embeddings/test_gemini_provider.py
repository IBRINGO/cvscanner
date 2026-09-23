from unittest.mock import Mock, patch

import pytest
import requests

from infrastructure.embeddings.base import EmbeddingProviderError
from infrastructure.embeddings.providers.gemini_provider import GeminiEmbeddingProvider


class TestGeminiEmbeddingProvider:
    def test_parses_embeddings_from_a_successful_response(self):
        provider = GeminiEmbeddingProvider(api_key="test-key", dimensions=3)
        fake_response = Mock()
        fake_response.raise_for_status = Mock()
        fake_response.json.return_value = {"embeddings": [{"values": [0.1, 0.2, 0.3]}]}

        target = "infrastructure.embeddings.providers.gemini_provider.requests.post"
        with patch(target, return_value=fake_response) as post:
            vectors = provider.embed(["hello"])

        assert vectors == [[0.1, 0.2, 0.3]]
        assert post.call_args.kwargs["params"]["key"] == "test-key"

    def test_network_failure_raises_embedding_provider_error(self):
        provider = GeminiEmbeddingProvider(api_key="test-key")

        target = "infrastructure.embeddings.providers.gemini_provider.requests.post"
        with patch(target, side_effect=requests.ConnectionError("no network")):
            with pytest.raises(EmbeddingProviderError):
                provider.embed(["hello"])

    def test_malformed_response_raises_embedding_provider_error(self):
        provider = GeminiEmbeddingProvider(api_key="test-key")
        fake_response = Mock()
        fake_response.raise_for_status = Mock()
        fake_response.json.return_value = {"unexpected": "shape"}

        target = "infrastructure.embeddings.providers.gemini_provider.requests.post"
        with patch(target, return_value=fake_response):
            with pytest.raises(EmbeddingProviderError):
                provider.embed(["hello"])

    def test_empty_text_list_never_calls_the_network(self):
        provider = GeminiEmbeddingProvider(api_key="test-key")
        target = "infrastructure.embeddings.providers.gemini_provider.requests.post"
        with patch(target) as post:
            assert provider.embed([]) == []
        post.assert_not_called()

    def test_reports_its_configured_model_as_its_name(self):
        provider = GeminiEmbeddingProvider(api_key="test-key", model="gemini-embedding-2")
        assert provider.name == "gemini-embedding-2"
