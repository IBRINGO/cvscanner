from unittest.mock import Mock, patch

import pytest
import requests

from infrastructure.embeddings.base import EmbeddingProviderError
from infrastructure.embeddings.providers.openai_provider import OpenAIEmbeddingProvider


class TestOpenAIEmbeddingProvider:
    def test_parses_embeddings_from_a_successful_response(self):
        provider = OpenAIEmbeddingProvider(api_key="test-key", dimensions=3)
        fake_response = Mock()
        fake_response.raise_for_status = Mock()
        fake_response.json.return_value = {"data": [{"embedding": [0.1, 0.2, 0.3]}]}

        target = "infrastructure.embeddings.providers.openai_provider.requests.post"
        with patch(target, return_value=fake_response) as post:
            vectors = provider.embed(["hello"])

        assert vectors == [[0.1, 0.2, 0.3]]
        assert post.call_args.kwargs["headers"]["Authorization"] == "Bearer test-key"

    def test_network_failure_raises_embedding_provider_error_not_a_raw_exception(self):
        provider = OpenAIEmbeddingProvider(api_key="test-key")

        with patch(
            "infrastructure.embeddings.providers.openai_provider.requests.post",
            side_effect=requests.ConnectionError("no network"),
        ):
            with pytest.raises(EmbeddingProviderError):
                provider.embed(["hello"])

    def test_malformed_response_raises_embedding_provider_error(self):
        provider = OpenAIEmbeddingProvider(api_key="test-key")
        fake_response = Mock()
        fake_response.raise_for_status = Mock()
        fake_response.json.return_value = {"unexpected": "shape"}

        target = "infrastructure.embeddings.providers.openai_provider.requests.post"
        with patch(target, return_value=fake_response):
            with pytest.raises(EmbeddingProviderError):
                provider.embed(["hello"])

    def test_empty_text_list_never_calls_the_network(self):
        provider = OpenAIEmbeddingProvider(api_key="test-key")
        with patch("infrastructure.embeddings.providers.openai_provider.requests.post") as post:
            assert provider.embed([]) == []
        post.assert_not_called()
