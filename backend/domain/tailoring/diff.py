"""Word-level diff computation (Phase 5 section 29). Pure stdlib
(`difflib`, no external dependency) - the domain layer stays
framework-free.
"""
import difflib

from domain.tailoring.entities import DiffSegment
from domain.tailoring.enums import ChangeType


def compute_word_diff(original_text: str, proposed_text: str) -> tuple[DiffSegment, ...]:
    original_words = original_text.split()
    proposed_words = proposed_text.split()
    matcher = difflib.SequenceMatcher(a=original_words, b=proposed_words, autojunk=False)

    segments: list[DiffSegment] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            segments.append(
                DiffSegment(text=" ".join(original_words[i1:i2]), change_type=ChangeType.UNCHANGED)
            )
        elif tag == "delete":
            segments.append(DiffSegment(text=" ".join(original_words[i1:i2]), change_type=ChangeType.REMOVED))
        elif tag == "insert":
            segments.append(DiffSegment(text=" ".join(proposed_words[j1:j2]), change_type=ChangeType.ADDED))
        elif tag == "replace":
            segments.append(DiffSegment(text=" ".join(original_words[i1:i2]), change_type=ChangeType.REMOVED))
            segments.append(DiffSegment(text=" ".join(proposed_words[j1:j2]), change_type=ChangeType.ADDED))
    return tuple(segments)
