"""Rule-based CandidateProfile extraction (sections 14-19 of the Phase 2
brief).

This is a deterministic v1: it reads the sections domain/cv/policies.py
already detected and applies simple, explainable heuristics (first line
is probably the name, "Technologies:" prefixes a tech list, etc). Real
CVs vary wildly in layout, so this will not perfectly structure every
document - see docs/architecture/phase-2-pipeline.md "Known limitations"
for what is intentionally out of scope for a rule-based first version.

Every structured fact (Experience, Education, ...) carries its own
Evidence (attached directly on the dataclass - see domain/cv/entities.py).
Document-level facts that don't map onto one list item (full_name,
contact, summary) have their Evidence returned separately in the second
return value.
"""
import re
from collections.abc import Mapping

from domain.cv.entities import (
    CandidateProfile,
    CandidateSkillMention,
    Certification,
    Contact,
    Education,
    Experience,
    Language,
    Project,
)
from domain.documents.entities import DetectedSection, ParsedDocument
from domain.documents.enums import ExtractionMethod, SectionType
from domain.documents.evidence import Evidence
from domain.skills.entities import Skill
from domain.skills.normalization import normalize_skill_name
from infrastructure.document_processing.extraction.text_extractor import (
    extract_email,
    extract_links,
    extract_phone,
    split_delimited_tokens,
)

_SECTION_CONFIDENCE = 0.9
_HEURISTIC_CONFIDENCE = 0.6
_CONTACT_CONFIDENCE = 0.85
_SKILL_MATCHED_CONFIDENCE = 0.95
_SKILL_UNMATCHED_CONFIDENCE = 0.5

_DATE_RANGE_RE = re.compile(
    r"^(?P<start>[A-Za-z]+\.?\s*\d{4}|\d{4})\s*[-–—]\s*"
    r"(?P<end>[A-Za-z]+\.?\s*\d{4}|\d{4}|present|current)\s*$",
    re.IGNORECASE,
)


class RuleBasedCandidateExtractor:
    """Implements infrastructure.document_processing.extraction.base.CandidateExtractor."""

    def __init__(self, skill_alias_index: Mapping[str, Skill]) -> None:
        self._skill_alias_index = skill_alias_index

    def extract(
        self, *, document_id: str, parsed: ParsedDocument, sections: list[DetectedSection]
    ) -> tuple[CandidateProfile, list[Evidence]]:
        document_level_evidence: list[Evidence] = []
        by_type = _group_by_type(sections)
        header_section = (
            sections[0] if sections and sections[0].section_type == SectionType.OTHER else None
        )

        full_name = _guess_full_name(parsed.raw_text)
        if full_name:
            document_level_evidence.append(
                Evidence(
                    source_document_id=document_id,
                    text=full_name,
                    extraction_method=ExtractionMethod.RULE,
                    confidence=_HEURISTIC_CONFIDENCE,
                    page_number=parsed.pages[0].page_number if parsed.pages else None,
                    metadata={"field": "full_name"},
                )
            )

        contact, contact_evidence = _extract_contact(document_id, header_section, parsed)
        document_level_evidence.extend(contact_evidence)

        summary = None
        if summary_section := by_type.get(SectionType.SUMMARY):
            summary = summary_section[0].body_text.strip() or None
            if summary:
                document_level_evidence.append(
                    _section_evidence(document_id, summary_section[0], summary)
                )

        experiences = [
            experience
            for section in by_type.get(SectionType.EXPERIENCE, [])
            for block in _split_blocks(section.body_text)
            if (experience := _parse_experience_block(document_id, section, block)) is not None
        ]

        education = [
            entry
            for section in by_type.get(SectionType.EDUCATION, [])
            for block in _split_blocks(section.body_text)
            if (entry := _parse_education_block(document_id, section, block)) is not None
        ]

        projects = [
            project
            for section in by_type.get(SectionType.PROJECTS, [])
            for block in _split_blocks(section.body_text)
            if (project := _parse_project_block(document_id, section, block)) is not None
        ]

        certifications = [
            certification
            for section in by_type.get(SectionType.CERTIFICATIONS, [])
            for line in section.body_text.split("\n")
            if line.strip()
            if (certification := _parse_certification_line(document_id, section, line)) is not None
        ]

        languages = [
            language
            for section in by_type.get(SectionType.LANGUAGES, [])
            for line in section.body_text.split("\n")
            if line.strip()
            if (language := _parse_language_line(document_id, section, line)) is not None
        ]

        skills: list[CandidateSkillMention] = []
        for section in by_type.get(SectionType.SKILLS, []):
            for token in split_delimited_tokens(section.body_text):
                skill = normalize_skill_name(token, self._skill_alias_index)
                evidence = Evidence(
                    source_document_id=document_id,
                    text=token,
                    extraction_method=ExtractionMethod.RULE,
                    confidence=_SKILL_MATCHED_CONFIDENCE if skill else _SKILL_UNMATCHED_CONFIDENCE,
                    page_number=section.page_number,
                    section=SectionType.SKILLS,
                    metadata={"matched": skill is not None},
                )
                skills.append(CandidateSkillMention(raw_text=token, skill=skill, evidence=evidence))

        profile = CandidateProfile(
            full_name=full_name,
            contact=contact,
            summary=summary,
            experiences=tuple(experiences),
            education=tuple(education),
            skills=tuple(skills),
            projects=tuple(projects),
            certifications=tuple(certifications),
            languages=tuple(languages),
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


def _guess_full_name(raw_text: str) -> str | None:
    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if "@" in stripped or any(char.isdigit() for char in stripped):
            return None  # first meaningful line looks like contact info, not a name
        word_count = len(stripped.split())
        if 1 <= word_count <= 5 and len(stripped) <= 60:
            return stripped
        return None
    return None


def _extract_contact(
    document_id: str, header_section: DetectedSection | None, parsed: ParsedDocument
) -> tuple[Contact, list[Evidence]]:
    search_text = header_section.body_text if header_section else parsed.raw_text
    evidence: list[Evidence] = []
    page_number = header_section.page_number if header_section else (
        parsed.pages[0].page_number if parsed.pages else None
    )

    email = extract_email(search_text) or extract_email(parsed.raw_text)
    phone = extract_phone(search_text) or extract_phone(parsed.raw_text)
    links = extract_links(parsed.raw_text)
    location = _guess_location(search_text)

    for field_name, value in (("email", email), ("phone", phone), ("location", location)):
        if value:
            evidence.append(
                Evidence(
                    source_document_id=document_id,
                    text=value,
                    extraction_method=ExtractionMethod.REGEX,
                    confidence=_CONTACT_CONFIDENCE,
                    page_number=page_number,
                    metadata={"field": field_name},
                )
            )

    return Contact(email=email, phone=phone, location=location, links=links), evidence


def _guess_location(text: str) -> str | None:
    for line in text.splitlines()[:8]:
        stripped = line.strip()
        if not stripped or "@" in stripped:
            continue
        if "," in stripped and len(stripped) <= 40 and not any(char.isdigit() for char in stripped):
            return stripped
    return None


def _split_blocks(body_text: str) -> list[str]:
    return [block.strip() for block in body_text.split("\n\n") if block.strip()]


def _split_title_company(header: str) -> tuple[str | None, str | None]:
    for separator in (" at ", " | ", " - ", ", "):
        if separator in header:
            title, company = header.split(separator, 1)
            return title.strip() or None, company.strip() or None
    return header.strip() or None, None


def _split_date_range(line: str) -> tuple[str, str] | None:
    match = _DATE_RANGE_RE.match(line.strip())
    if not match:
        return None
    return match.group("start").strip(), match.group("end").strip()


def _parse_experience_block(
    document_id: str, section: DetectedSection, block: str
) -> Experience | None:
    lines = [line.strip() for line in block.split("\n") if line.strip()]
    if not lines:
        return None

    title, company = _split_title_company(lines[0])
    remaining = lines[1:]
    start_date = end_date = None
    if remaining and (dates := _split_date_range(remaining[0])):
        start_date, end_date = dates
        remaining = remaining[1:]

    achievements: list[str] = []
    technologies: list[str] = []
    description_lines: list[str] = []
    for line in remaining:
        if line.lower().startswith("technologies:"):
            technologies = split_delimited_tokens(line.split(":", 1)[1])
        elif line.startswith(("-", "•", "*")):
            achievements.append(line.lstrip("-•* ").strip())
        else:
            description_lines.append(line)

    return Experience(
        title=title,
        company=company,
        start_date_raw=start_date,
        end_date_raw=end_date,
        description=" ".join(description_lines) or None,
        achievements=tuple(achievements),
        technologies=tuple(technologies),
        evidence=_section_evidence(document_id, section, block),
    )


def _parse_education_block(
    document_id: str, section: DetectedSection, block: str
) -> Education | None:
    lines = [line.strip() for line in block.split("\n") if line.strip()]
    if not lines:
        return None

    degree, institution = _split_title_company(lines[0])
    remaining = lines[1:]
    start_date = end_date = None
    if remaining and (dates := _split_date_range(remaining[0])):
        start_date, end_date = dates

    return Education(
        institution=institution,
        degree=degree,
        field_of_study=None,
        start_date_raw=start_date,
        end_date_raw=end_date,
        evidence=_section_evidence(document_id, section, block),
    )


def _parse_project_block(document_id: str, section: DetectedSection, block: str) -> Project | None:
    lines = [line.strip() for line in block.split("\n") if line.strip()]
    if not lines:
        return None

    name = lines[0]
    technologies: list[str] = []
    description_lines: list[str] = []
    for line in lines[1:]:
        if line.lower().startswith("technologies:"):
            technologies = split_delimited_tokens(line.split(":", 1)[1])
        else:
            description_lines.append(line)

    return Project(
        name=name,
        description=" ".join(description_lines) or None,
        technologies=tuple(technologies),
        evidence=_section_evidence(document_id, section, block),
    )


def _parse_certification_line(
    document_id: str, section: DetectedSection, line: str
) -> Certification | None:
    parts = [part.strip() for part in line.split(",")]
    if not parts or not parts[0]:
        return None
    return Certification(
        name=parts[0],
        issuer=parts[1] if len(parts) > 1 else None,
        date_raw=parts[2] if len(parts) > 2 else None,
        evidence=_section_evidence(document_id, section, line),
    )


def _parse_language_line(document_id: str, section: DetectedSection, line: str) -> Language | None:
    for separator in (" - ", "(", ":"):
        if separator in line:
            name, proficiency = line.split(separator, 1)
            return Language(
                name=name.strip(),
                proficiency=proficiency.strip(" )") or None,
                evidence=_section_evidence(document_id, section, line),
            )
    stripped = line.strip()
    if not stripped:
        return None
    return Language(name=stripped, proficiency=None, evidence=_section_evidence(document_id, section, line))
