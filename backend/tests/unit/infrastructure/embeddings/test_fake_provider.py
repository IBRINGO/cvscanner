from infrastructure.embeddings.providers.fake_provider import FakeEmbeddingProvider


class TestFakeEmbeddingProvider:
    def test_returns_one_vector_per_text_with_configured_dimensions(self):
        provider = FakeEmbeddingProvider(dimensions=16)
        vectors = provider.embed(["hello", "world"])
        assert len(vectors) == 2
        assert all(len(vector) == 16 for vector in vectors)

    def test_deterministic_for_the_same_text(self):
        provider = FakeEmbeddingProvider()
        assert provider.embed(["same text"]) == provider.embed(["same text"])

    def test_different_text_yields_different_vectors(self):
        provider = FakeEmbeddingProvider()
        vectors = provider.embed(["Django developer", "React developer"])
        assert vectors[0] != vectors[1]

    def test_vector_components_are_within_expected_range(self):
        provider = FakeEmbeddingProvider()
        [vector] = provider.embed(["anything"])
        assert all(-1.0 <= value <= 1.0 for value in vector)

    def test_reports_its_own_name_and_dimensions(self):
        provider = FakeEmbeddingProvider(dimensions=8)
        assert provider.name == "fake"
        assert provider.dimensions == 8

    def test_empty_text_list_returns_empty(self):
        assert FakeEmbeddingProvider().embed([]) == []
