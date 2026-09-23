"""Enumerations for the Phase 5 recommendation engine.

Kept as stdlib `enum.StrEnum` subclasses - same convention as
domain/matching/enums.py - so this module stays importable from
anywhere (Django admin choices, DRF serializers, tests) without
creating a reverse dependency.
"""
from enum import StrEnum


class RecommendationType(StrEnum):
    """What kind of finding a recommendation originates from. Each type
    maps to a specific Phase 4 signal - a recommendation is never
    generated from something the matching engine did not actually find.
    """

    MISSING_REQUIREMENT = "MISSING_REQUIREMENT"
    WEAK_EVIDENCE = "WEAK_EVIDENCE"
    UNDERREPRESENTED_SKILL = "UNDERREPRESENTED_SKILL"
    EXPERIENCE_CLARIFICATION = "EXPERIENCE_CLARIFICATION"
    KEYWORD_PLACEMENT = "KEYWORD_PLACEMENT"
    RESPONSIBILITY_ALIGNMENT = "RESPONSIBILITY_ALIGNMENT"
    CERTIFICATION_GAP = "CERTIFICATION_GAP"
    LANGUAGE_GAP = "LANGUAGE_GAP"
    SENIORITY_CLARIFICATION = "SENIORITY_CLARIFICATION"


class RecommendationPriority(StrEnum):
    """Structured priority - see domain/recommendations/engine.py for how
    this is derived from requirement priority, match signal, and evidence
    quality. Never derived from keyword frequency (section 8 of the
    brief).
    """

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RecommendationConfidence(StrEnum):
    """Reflects evidence quality behind the recommendation itself - this
    is a distinct axis from RecommendationPriority (section 9: "do not
    confuse confidence with recommendation priority"). A CRITICAL
    recommendation about a completely missing mandatory skill can still
    have HIGH confidence (the gap is unambiguous); a LOW-priority
    clarification suggestion can have LOW confidence if the supporting
    evidence is thin.
    """

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RecommendationSafety(StrEnum):
    """Whether - and how - this recommendation could be automated by the
    Tailoring Engine (section 11). This is the field that keeps
    recommendations and tailoring honest about what is actually safe to
    rewrite automatically versus what only a human (or nothing) can
    resolve.
    """

    SAFE_TO_REPHRASE = "SAFE_TO_REPHRASE"
    SAFE_TO_REORDER = "SAFE_TO_REORDER"
    REQUIRES_CANDIDATE_CONFIRMATION = "REQUIRES_CANDIDATE_CONFIRMATION"
    NOT_SAFE_TO_AUTOMATE = "NOT_SAFE_TO_AUTOMATE"


class RecommendationImpact(StrEnum):
    """A qualitative estimate of relevance to THIS analysis (section 13).
    Never a promised score delta - see domain/recommendations/engine.py's
    module docstring.
    """

    HIGH_IMPACT = "HIGH_IMPACT"
    MEDIUM_IMPACT = "MEDIUM_IMPACT"
    LOW_IMPACT = "LOW_IMPACT"
