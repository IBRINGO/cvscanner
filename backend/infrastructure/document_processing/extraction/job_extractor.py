"""Rule-based JobProfile extraction (sections 21-23 of the Phase 2 brief).

Mirrors candidate_extractor.py's approach: deterministic heuristics over
the sections domain/cv/policies.py detected, every JobRequirement carries
its own Evidence directly (see domain/job/entities.py). Explicitly does
not compare anything to a CandidateProfile - see section 24/25 of the
brief. A JobRequirement here is just a classified statement; nothing here
decides whether any candidate satisfies it.
"""
import re
from collections.abc import Mapping

from domain.documents.entities import DetectedSection, ParsedDocument
from domain.documents.enums import ExtractionMethod, SectionType
from domain.documents.evidence import Evidence
from domain.job.entities import JobProfile, JobRequirement
from domain.job.enums import RequirementImportance, RequirementType
from domain.skills.entities import Skill
from domain.skills.normalization import normalize_skill_name

_SECTION_CONFIDENCE = 0.9
_HEURISTIC_CONFIDENCE = 0.6
_SKILL_MATCHED_CONFIDENCE = 0.95

_LABEL_FIELDS = {
    "company": "company",
    "location": "location",
    "employment type": "employment_type",
    "seniority": "seniority",
}
_EXPERIENCE_RE = re.compile(r"\d+\+?\s*(?:years?|yrs?)", re.IGNORECASE)
_EDUCATION_RE = re.compile(r"\b(bachelor|master|phd|degree|diploma)\b", re.IGNORECASE)
_REQUIRED_MARKERS = {"required", "must have", "requirements"}
_PREFERRED_MARKERS = {"preferred", "nice to have", "bonus"}


class RuleBasedJobExtractor:
    """Implements infrastructure.document_processing.extraction.base.JobExtractor."""

    def __init__(self, skill_alias_index: Mapping[str, Skill]) -> None:
        self._skill_alias_index = skill_alias_index

    def extract(
        self, *, document_id: str, parsed: ParsedDocument, sections: list[DetectedSection]
    ) -> tuple[JobProfile, list[Evidence]]:
        document_level_evidence: list[Evidence] = []
        by_type = _group_by_type(sections)
        header_section = (
            sections[0] if sections and sections[0].section_type == SectionType.OTHER else None
        )

        title = _guess_title(parsed.raw_text)
        if title:
            document_level_evidence.append(
                Evidence(
                    source_document_id=document_id,
                    text=title,
                    extraction_method=ExtractionMethod.RULE,
                    confidence=_HEURISTIC_CONFIDENCE,
                    metadata={"field": "title"},
                )
            )

        labels = _extract_labeled_fields(header_section.body_text if header_section else "")
        for field_name, value in labels.items():
            document_level_evidence.append(
                Evidence(
                    source_document_id=document_id,
                    text=value,
                    extraction_method=ExtractionMethod.RULE,
                    confidence=_SECTION_CONFIDENCE,
                    page_number=header_section.page_number if header_section else None,
                    metadata={"field": field_name},
                )
            )

        summary = None
        if summary_section := by_type.get(SectionType.SUMMARY):
            summary = summary_section[0].body_text.strip() or None
            if summary:
                document_level_evidence.append(
                    _section_evidence(document_id, summary_section[0], summary)
                )

        responsibilities: list[str] = []
        for section in by_type.get(SectionType.RESPONSIBILITIES, []):
            responsibilities.extend(_bullet_lines(section.body_text))

        requirements = [
            requirement
            for section in by_type.get(SectionType.REQUIREMENTS, [])
            for requirement in _parse_requirements(document_id, section, self._skill_alias_index)
        ]

        profile = JobProfile(
            title=title,
            company=labels.get("company"),
            location=labels.get("location"),
            employment_type=labels.get("employment_type"),
            seniority=labels.get("seniority"),
            summary=summary,
            responsibilities=tuple(responsibilities),
            requirements=tuple(requirements),
        )
        return profile, document_level_evidence


def _group_by_type(sections: list[DetectedSection]) -> dict[SectionType, list[DetectedSection]]:
    grouped: dict[SectionType, list[DetectedSection]] = {}
    for section in sections:
        grouped.setdefault(section.section_type, []).append(section)
    return grouped


def _section_evidence(document_id: str, section: DetectedSection, text: str) -> Evidence:
    return Evidence(
        source_document_id=document_id,
        text=text[:500],
        extraction_method=ExtractionMethod.RULE,
        confidence=_SECTION_CONFIDENCE,
        page_number=section.page_number,
        section=section.section_type,
    )


def _guess_title(raw_text: str) -> str | None:
    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if ":" in stripped or len(stripped) > 80:
            return None
        return stripped
    return None


def _extract_labeled_fields(header_text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in header_text.splitlines():
        if ":" not in line:
            continue
        label, _, value = line.partition(":")
        key = _LABEL_FIELDS.get(label.strip().lower())
        if key and value.strip():
            fields[key] = value.strip()
    return fields


def _bullet_lines(body_text: str) -> list[str]:
    lines = [line.strip() for line in body_text.split("\n") if line.strip()]
    return [line.lstrip("-•* ").strip() for line in lines]


def _parse_requirements(
    document_id: str, section: DetectedSection, skill_alias_index: Mapping[str, Skill]
) -> list[JobRequirement]:
    results: list[JobRequirement] = []
    importance = RequirementImportance.REQUIRED

    for raw_line in section.body_text.split("\n"):
        line = raw_line.strip().lstrip("-•* ").strip()
        if not line:
            continue

        normalized = line.rstrip(":").strip().lower()
        if normalized in _REQUIRED_MARKERS:
            importance = RequirementImportance.REQUIRED
            continue
        if normalized in _PREFERRED_MARKERS:
            importance = RequirementImportance.PREFERRED
            continue

        results.append(
            _classify_requirement(document_id, section, line, importance, skill_alias_index)
        )

    return results


def _classify_requirement(
    document_id: str,
    section: DetectedSection,
    line: str,
    importance: RequirementImportance,
    skill_alias_index: Mapping[str, Skill],
) -> JobRequirement:
    skill = normalize_skill_name(line, skill_alias_index)
    evidence = Evidence(
        source_document_id=document_id,
        text=line,
        extraction_method=ExtractionMethod.RULE,
        confidence=_SKILL_MATCHED_CONFIDENCE if skill else _SECTION_CONFIDENCE,
        page_number=section.page_number,
        section=SectionType.REQUIREMENTS,
    )

    if skill:
        req_type = (
            RequirementType.REQUIRED_SKILL
            if importance == RequirementImportance.REQUIRED
            else RequirementType.PREFERRED_SKILL
        )
        return JobRequirement(
            requirement_type=req_type, importance=importance, raw_text=line, skill=skill, evidence=evidence
        )

    if _EXPERIENCE_RE.search(line):
        return JobRequirement(
            requirement_type=RequirementType.EXPERIENCE,
            importance=importance,
            raw_text=line,
            evidence=evidence,
        )

    if _EDUCATION_RE.search(line):
        return JobRequirement(
            requirement_type=RequirementType.EDUCATION,
            importance=importance,
            raw_text=line,
            evidence=evidence,
        )

    return JobRequirement(
        requirement_type=RequirementType.OTHER, importance=importance, raw_text=line, evidence=evidence
    )
