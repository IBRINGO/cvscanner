"""Enumerations for the Truth Layer (Phase 5 sections 14-18).

Kept as stdlib `enum.StrEnum` subclasses, same convention as every
other domain bounded context.
"""
from enum import StrEnum


class FactType(StrEnum):
    """What kind of candidate fact this is. Mirrors the CandidateProfile
    sections that already carry evidence (domain/cv/entities.py) rather
    than inventing a parallel taxonomy.
    """

    SKILL = "SKILL"
    EXPERIENCE = "EXPERIENCE"
    EDUCATION = "EDUCATION"
    CERTIFICATION = "CERTIFICATION"
    LANGUAGE = "LANGUAGE"
    PROJECT = "PROJECT"


class VerificationStatus(StrEnum):
    """How trustworthy a fact is for automatic content generation
    (section 16). Only VERIFIED and SUPPORTED facts may be used as the
    basis for LLM-generated wording (section 17) - INFERRED and UNKNOWN
    facts may only ever be *presented as gaps*, never written into
    generated CV content as if they were confirmed.
    """

    VERIFIED = "VERIFIED"
    SUPPORTED = "SUPPORTED"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"


class AllowedTransformation(StrEnum):
    """What is permitted to happen to a fact's wording (section 17).
    There is no enum member for the forbidden transformations
    (INVENT, SPECULATE, UPGRADE_LEVEL, ADD_UNSUPPORTED_TECHNOLOGY,
    ADD_UNSUPPORTED_CERTIFICATION, ADD_UNSUPPORTED_DURATION) on purpose -
    they are not values this system can select, only violations
    `domain/truth/claim_validation.py` detects and rejects.
    """

    REORDER = "REORDER"
    REPHRASE = "REPHRASE"
    SUMMARIZE = "SUMMARIZE"
    CONDENSE = "CONDENSE"
    EXPAND_WITH_EXISTING_EVIDENCE = "EXPAND_WITH_EXISTING_EVIDENCE"


class ClaimRejectionReason(StrEnum):
    """Why a generated claim was rejected by claim_validation.py -
    surfaced to the user per section 57 ("explain, don't hide").
    """

    UNSUPPORTED_TECHNOLOGY = "UNSUPPORTED_TECHNOLOGY"
    UNSUPPORTED_CERTIFICATION = "UNSUPPORTED_CERTIFICATION"
    DURATION_INFLATION = "DURATION_INFLATION"
    EDUCATION_UPGRADE = "EDUCATION_UPGRADE"
    LANGUAGE_PROFICIENCY_UPGRADE = "LANGUAGE_PROFICIENCY_UPGRADE"
    SENIORITY_UPGRADE = "SENIORITY_UPGRADE"
    DATE_MODIFIED = "DATE_MODIFIED"
