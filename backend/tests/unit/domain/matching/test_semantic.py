from domain.matching.semantic import cosine_similarity


class TestCosineSimilarity:
    def test_identical_vectors_have_similarity_one(self):
        assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0

    def test_orthogonal_vectors_have_similarity_zero(self):
        assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0

    def test_opposite_vectors_have_similarity_negative_one(self):
        assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == -1.0

    def test_zero_vector_returns_zero_rather_than_dividing_by_zero(self):
        assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0

    def test_mismatched_lengths_return_zero(self):
        assert cosine_similarity([1.0], [1.0, 2.0]) == 0.0

    def test_empty_vectors_return_zero(self):
        assert cosine_similarity([], []) == 0.0
