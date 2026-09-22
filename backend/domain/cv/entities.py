"""Canonical CandidateProfile representation (section 14 of the Phase 2
brief). All fields but `full_name` are optional - a CV rarely has every
section, and the extractor must not invent data to fill gaps.

Each structured fact (Experience, Education, Project, Certification,
Language, CandidateSkillMention) carries its own `evidence` - the
provenance record for exactly that fact (section 15). Document-level
facts that don't map onto one list item (full_name, contact fields,
summary) are not embedded here; their evidence is returned alongside the
profile by the extractor instead - see
infrastructure/document_processing/extraction/candidate_extractor.py.

Phase 3 added `seniority`/`degree_level`/`canonical_name`/
`proficiency_normalized` - values derived from the fields already here
(see application/semantics/enrich_candidate_profile.py), never replacing
them. Phase 4's matching engine (domain/matching/) reads these directly
instead of re-deriving them.
"""
from dataclasses import dataclass, field

from domain.cv.education_normalization import EducationLevel
from domain.cv.language_normalization import LanguageProficiency
from domain.cv.seniority import SeniorityLevel
from domain.documents.evidence import Evidence
from domain.skills.entities import Skill


@dataclass(frozen=True)
class Contact:
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    links: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Experience:
    title: str | None
    company: str | None
    start_date_raw: str | None
    end_date_raw: str | None
    description: str | None
    achievements: tuple[str, ...] = field(default_factory=tuple)
    technologies: tuple[str, ...] = field(default_factory=tuple)
    seniority: SeniorityLevel | None = None
    evidence: Evidence | None = None


@dataclass(frozen=True)
class Education:
    institution: str | None
    degree: str | None
    field_of_study: str | None
    start_date_raw: str | None
    end_date_raw: str | None
    degree_level: EducationLevel | None = None
    evidence: Evidence | None = None


@dataclass(frozen=True)
class Project:
    name: str
    description: str | None
    technologies: tuple[str, ...] = field(default_factory=tuple)
    evidence: Evidence | None = None


@dataclass(frozen=True)
class Certification:
    name: str
    issuer: str | None
    date_raw: str | None
    evidence: Evidence | None = None


@dataclass(frozen=True)
class Language:
    name: str
    proficiency: str | None = None
    canonical_name: str | None = None
    proficiency_normalized: LanguageProficiency | None = None
    evidence: Evidence | None = None


@dataclass(frozen=True)
class CandidateSkillMention:
    """One skill as it appeared on the CV. `skill` is the normalized
    canonical Skill if the taxonomy recognized `raw_text` (see
    domain/skills/normalization.py); otherwise `skill` is None and
    `raw_text` is kept as-is rather than force-matched to something
    plausible-looking.
    """

    raw_text: str
    skill: Skill | None
    evidence: Evidence | None = None


@dataclass(frozen=True)
class CandidateProfile:
    full_name: str | None
    contact: Contact
    summary: str | None
    experiences: tuple[Experience, ...] = field(default_factory=tuple)
    education: tuple[Education, ...] = field(default_factory=tuple)
    skills: tuple[CandidateSkillMention, ...] = field(default_factory=tuple)
    projects: tuple[Project, ...] = field(default_factory=tuple)
    certifications: tuple[Certification, ...] = field(default_factory=tuple)
    languages: tuple[Language, ...] = field(default_factory=tuple)
