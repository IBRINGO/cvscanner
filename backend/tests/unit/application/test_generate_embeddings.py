from application.semantics.generate_embeddings import GenerateSemanticEmbeddings
from domain.semantics.enums import SemanticEntityType
from infrastructure.embeddings.base import EmbeddingProviderError


class FakeProvider:
    name = "fake"
    dimensions = 4

    def __init__(self, error=None):
        self._error = error

    def embed(self, texts):
        if self._error:
            raise self._error
        return [[0.1, 0.2, 0.3, 0.4] for _ in texts]


class FakeRepository:
    def __init__(self):
        self.saved = None

    def save(self, representation):
        self.saved = representation


class TestGenerateSemanticEmbeddings:
    def test_saves_a_representation_for_nonempty_text(self):
        repository = FakeRepository()
        use_case = GenerateSemanticEmbeddings(FakeProvider(), repository)

        use_case.execute(SemanticEntityType.CANDIDATE_PROFILE, "doc-1", "Backend engineer skilled in Django")

        assert repository.saved is not None
        assert repository.saved.entity_id == "doc-1"
        assert repository.saved.dimensions == 4
        assert repository.saved.model == "fake"

    def test_blank_text_is_skipped_without_calling_the_provider(self):
        repository = FakeRepository()
        use_case = GenerateSemanticEmbeddings(FakeProvider(), repository)

        use_case.execute(SemanticEntityType.JOB_PROFILE, "doc-1", "   ")

        assert repository.saved is None

    def test_provider_failure_degrades_without_raising(self):
        repository = FakeRepository()
        use_case = GenerateSemanticEmbeddings(FakeProvider(error=EmbeddingProviderError("down")), repository)

        use_case.execute(SemanticEntityType.CANDIDATE_PROFILE, "doc-1", "some text")  # must not raise

        assert repository.saved is None

    def test_unexpected_provider_error_also_degrades_without_raising(self):
        repository = FakeRepository()
        use_case = GenerateSemanticEmbeddings(FakeProvider(error=RuntimeError("boom")), repository)

        use_case.execute(SemanticEntityType.CANDIDATE_PROFILE, "doc-1", "some text")  # must not raise

        assert repository.saved is None
