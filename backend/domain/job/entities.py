"""Canonical JobProfile representation (sections 21-22 of the Phase 2
brief). No matching or scoring concept appears here - a JobRequirement is
just a classified, evidence-backed statement extracted from the offer.

Phase 3 added `seniority_normalized`/`minimum_years`/`normalized_value` -
derived from the fields already here (see
application/semantics/enrich_job_profile.py), never replacing them.
Phase 4's matching engine (domain/matching/) reads these directly.
"""
from dataclasses import dataclass, field

from domain.cv.seniority import SeniorityLevel
from domain.documents.evidence import Evidence
from domain.job.enums import RequirementImportance, RequirementType
from domain.skills.entities import Skill


@dataclass(frozen=True)
class JobRequirement:
    requirement_type: RequirementType
    importance: RequirementImportance
    raw_text: str
    skill: Skill | None = None
    minimum_years: int | None = None
    normalized_value: str | None = None
    evidence: Evidence | None = None


@dataclass(frozen=True)
class JobProfile:
    title: str | None
    company: str | None
    location: str | None
    employment_type: str | None
    seniority: str | None
    summary: str | None
    seniority_normalized: SeniorityLevel | None = None
    responsibilities: tuple[str, ...] = field(default_factory=tuple)
    requirements: tuple[JobRequirement, ...] = field(default_factory=tuple)
