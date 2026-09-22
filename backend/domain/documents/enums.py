"""Enumerations for the document ingestion/parsing bounded context.

Kept as stdlib `enum.StrEnum` subclasses so this module stays importable
from anywhere, including infrastructure/Django code, without creating a
reverse dependency.
"""
from enum import StrEnum


class DocumentType(StrEnum):
    CV = "CV"
    JOB_OFFER = "JOB_OFFER"


class ProcessingStatus(StrEnum):
    UPLOADED = "UPLOADED"
    VALIDATING = "VALIDATING"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class ExtractionMethod(StrEnum):
    """How a specific fact (a skill, a requirement, an experience entry...)
    was derived. See domain/documents/evidence.py for how this is used.

    Phase 2 only produces PARSER/RULE/REGEX facts. MANUAL, LLM, and HYBRID
    are reserved for later phases (manual correction UI, LLM-assisted
    extraction) - the enum exists now so evidence records never need a
    schema change to support them.
    """

    PARSER = "PARSER"
    RULE = "RULE"
    REGEX = "REGEX"
    MANUAL = "MANUAL"
    LLM = "LLM"
    HYBRID = "HYBRID"


class SectionType(StrEnum):
    """Canonical section categories a parsed document can be split into.

    Shared by both CVs and job offers - a job offer's "Requirements"
    heading and a CV's "Experience" heading both need to normalize to one
    of these before extraction can reason about them. See
    domain/cv/policies.py for the raw-heading -> SectionType mapping.
    """

    SUMMARY = "SUMMARY"
    EXPERIENCE = "EXPERIENCE"
    EDUCATION = "EDUCATION"
    SKILLS = "SKILLS"
    PROJECTS = "PROJECTS"
    CERTIFICATIONS = "CERTIFICATIONS"
    LANGUAGES = "LANGUAGES"
    ACHIEVEMENTS = "ACHIEVEMENTS"
    PUBLICATIONS = "PUBLICATIONS"
    VOLUNTEER_EXPERIENCE = "VOLUNTEER_EXPERIENCE"
    RESPONSIBILITIES = "RESPONSIBILITIES"
    REQUIREMENTS = "REQUIREMENTS"
    OTHER = "OTHER"
