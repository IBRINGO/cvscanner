from domain.tailoring.diff import compute_word_diff
from domain.tailoring.enums import ChangeType


class TestComputeWordDiff:
    def test_identical_text_is_entirely_unchanged(self):
        diff = compute_word_diff("Built APIs with Django.", "Built APIs with Django.")
        assert all(segment.change_type == ChangeType.UNCHANGED for segment in diff)

    def test_an_added_phrase_is_marked_added(self):
        diff = compute_word_diff("Built APIs.", "Built REST APIs.")
        added = [s.text for s in diff if s.change_type == ChangeType.ADDED]
        assert "REST" in " ".join(added)

    def test_a_removed_phrase_is_marked_removed(self):
        diff = compute_word_diff("Built REST APIs.", "Built APIs.")
        removed = [s.text for s in diff if s.change_type == ChangeType.REMOVED]
        assert "REST" in " ".join(removed)
