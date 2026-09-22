"""Enumerations for the Phase 4 matching/scoring bounded context. Kept
as stdlib `enum.StrEnum` subclasses so this module stays importable
from anywhere (Django admin choices, DRF serializers, tests) without
creating a reverse dependency - same convention as
domain/documents/enums.py.
"""
from enum import StrEnum


class MatchSignal(StrEnum):
    """How a requirement was resolved against the candidate's evidence.
    These are NOT interchangeable - see domain/matching/skill_matching.py
    for exactly how each is produced. Ordered here from strongest to
    weakest identity claim (see MatchStrength.for_signal below, which
    encodes that ordering numerically).
    """

    EXACT_MATCH = "EXACT_MATCH"
    ALIAS_MATCH = "ALIAS_MATCH"
    RELATED_MATCH = "RELATED_MATCH"
    SEMANTIC_MATCH = "SEMANTIC_MATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    NO_EVIDENCE = "NO_EVIDENCE"


class MatchStrength(StrEnum):
    """A normalized internal strength classification (section 22 of the
    Phase 4 brief) - the single scale every matcher maps its own signal
    onto, so the frontend and the scoring engine never have to reconcile
    several ad-hoc scales. Not a candidate ranking; a per-requirement
    classification.
    """

    NONE = "NONE"
    WEAK = "WEAK"
    PARTIAL = "PARTIAL"
    GOOD = "GOOD"
    STRONG = "STRONG"


class RequirementPriority(StrEnum):
    """Phase 2/3's JobRequirement only distinguishes REQUIRED/PREFERRED
    (domain.job.enums.RequirementImportance) - see
    domain/matching/priority.py for why OPTIONAL is a Phase 4-only
    addition rather than a change to that existing enum.
    """

    MANDATORY = "MANDATORY"
    PREFERRED = "PREFERRED"
    OPTIONAL = "OPTIONAL"


class RequirementStatus(StrEnum):
    MET = "MET"
    PARTIALLY_MET = "PARTIALLY_MET"
    NOT_MET = "NOT_MET"
    UNKNOWN = "UNKNOWN"


class AnalysisStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SeniorityComparison(StrEnum):
    """`UNKNOWN` is a distinct, legitimate outcome - section 12 of the
    brief is explicit that "unknown" must never be silently treated as
    "does not meet".
    """

    MEETS = "MEETS"
    EXCEEDS = "EXCEEDS"
    PARTIAL = "PARTIAL"
    BELOW = "BELOW"
    UNKNOWN = "UNKNOWN"


class EducationComparison(StrEnum):
    MEETS = "MEETS"
    EXCEEDS = "EXCEEDS"
    BELOW = "BELOW"
    UNKNOWN = "UNKNOWN"


class ProficiencyComparison(StrEnum):
    EXACT = "EXACT"
    HIGHER = "HIGHER"
    LOWER = "LOWER"
    PRESENT_UNKNOWN_LEVEL = "PRESENT_UNKNOWN_LEVEL"
    ABSENT = "ABSENT"
