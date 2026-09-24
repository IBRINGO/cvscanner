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

    Phase 2 produced PARSER/RULE/REGEX facts. Phase 3 adds ALIAS (a skill
    normalization decision - see domain/skills/normalization.py),
    TAXONOMY (a fact derived by scanning text against the skill taxonomy -
    see domain/skills/enrichment.py), and EMBEDDING (produced by an
    EmbeddingProvider - see infrastructure/embeddings/). MANUAL and LLM
    remain reserved for later phases (manual correction UI, LLM-assisted
    extraction).
    """

    PARSER = "PARSER"
    RULE = "RULE"
    REGEX = "REGEX"
    ALIAS = "ALIAS"
    TAXONOMY = "TAXONOMY"
    EMBEDDING = "EMBEDDING"
    MANUAL = "MANUAL"
    LLM = "LLM"
    HYBRID = "HYBRID"


class SectionType(StrEnum):
    """Canonical section categories a parsed document can be split into.

    Shared by both CVs and job offers - a job offer's "Requirements"
    heading and a CV's "Experience" heading both need to normalize to one
    of these before extraction can reason about them. See
    domain/cv/policies.py for the raw-heading -> SectionType mapping.

    The document-intelligence overhaul (see docs/architecture -
    "bilingual section taxonomy") added 11 members below PERSONAL_INFORMATION
    so real-world CV heading vocabulary (EN/FR) has a canonical home even
    when the rule-based extractors don't yet populate a dedicated
    CandidateProfile field for it - correct *segmentation* (a "Leadership"
    heading no longer gets swallowed into the preceding Experience entry)
    is the win, independent of whether a field exists yet.
    """

    PERSONAL_INFORMATION = "PERSONAL_INFORMATION"
    SUMMARY = "SUMMARY"
    HIGHLIGHTS = "HIGHLIGHTS"
    CORE_QUALIFICATIONS = "CORE_QUALIFICATIONS"
    EXPERIENCE = "EXPERIENCE"
    EDUCATION = "EDUCATION"
    PROJECTS = "PROJECTS"
    SKILLS = "SKILLS"
    TECHNICAL_SKILLS = "TECHNICAL_SKILLS"
    CERTIFICATIONS = "CERTIFICATIONS"
    LANGUAGES = "LANGUAGES"
    ACHIEVEMENTS = "ACHIEVEMENTS"
    PUBLICATIONS = "PUBLICATIONS"
    PRESENTATIONS = "PRESENTATIONS"
    VOLUNTEER_EXPERIENCE = "VOLUNTEER_EXPERIENCE"
    LEADERSHIP = "LEADERSHIP"
    INTERESTS = "INTERESTS"
    HOBBIES = "HOBBIES"
    AFFILIATIONS = "AFFILIATIONS"
    SCHOLARSHIPS = "SCHOLARSHIPS"
    ADDITIONAL_INFORMATION = "ADDITIONAL_INFORMATION"
    RESPONSIBILITIES = "RESPONSIBILITIES"
    REQUIREMENTS = "REQUIREMENTS"
    OTHER = "OTHER"


class DocumentLanguage(StrEnum):
    """The natural language a document is *written in* - distinct from
    domain/cv/language_normalization.py's `LanguageProficiency`, which is
    about a language the *candidate speaks* (a CV fact). See
    domain/documents/language.py for the detector that produces this.

    Deliberately just two real values today (the overhaul's initial
    scope) plus UNKNOWN for "could not tell" - never guessed. Adding a
    language later (Spanish, Arabic, German - see module docstring in
    domain/documents/language.py) is one new member here plus one new
    signal table, not a pipeline rewrite.
    """

    EN = "EN"
    FR = "FR"
    UNKNOWN = "UNKNOWN"
