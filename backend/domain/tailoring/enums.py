from enum import StrEnum


class TailoringMode(StrEnum):
    """Section 19. CONSERVATIVE never calls the LLM - every operation is
    a deterministic rewrite (alias normalization, reordering). Section 24
    is unambiguous that the LLM never becomes the source of truth, and
    CONSERVATIVE mode demonstrates that a large share of useful tailoring
    needs no generation at all. AGGRESSIVE_SAFE may call the LLM for
    bullet-level rewriting, but every proposal it returns still passes
    through the same Truth Layer validation as any other mode - "safe" is
    not a relaxation of that check, only a wider set of allowed
    operations (section 19: restructure, combine, emphasize, rewrite -
    never invent).
    """

    CONSERVATIVE = "CONSERVATIVE"
    AGGRESSIVE_SAFE = "AGGRESSIVE_SAFE"


class TailoringStatus(StrEnum):
    PENDING = "PENDING"
    PLANNING = "PLANNING"
    GENERATING = "GENERATING"
    VALIDATING = "VALIDATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ChangeType(StrEnum):
    """Word-level diff semantics (section 29)."""

    ADDED = "ADDED"
    REMOVED = "REMOVED"
    UNCHANGED = "UNCHANGED"
