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
import unicodedata
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

_MONTH_RE = (
    r"(?:jan(?:v(?:ier)?)?|f[eé]v(?:r(?:ier)?)?|mars?|avr(?:il)?|mai|juin?|juil(?:let)?|"
    r"ao[uû]t|sept(?:embre)?|oct(?:obre)?|nov(?:embre)?|d[eé]c(?:embre)?|january|february|"
    r"march|april|may|june|july|august|september|october|november|december)\.?"
)
_END_MARKERS_RE = r"present|current|pr[eé]sent|actuel(?:le)?|aujourd'?hui|en cours|[aà] ce jour"
_DATE_TOKEN_RE = rf"(?:{_MONTH_RE}\s*\d{{4}}|\d{{4}}|{_MONTH_RE})"

# A whole line that is JUST a date range - "January 2020 - Present",
# "2013 - 2017". Anchored on both ends so a header line that merely ENDS
# with a date (see _TRAILING_DATE_RANGE_RE below) never matches here -
# that ambiguity matters: "January 2020 - Present" must never be parsed
# as prefix="January", start="2020" (see _extract_date_range's ordering).
_DATE_RANGE_RE = re.compile(
    rf"^(?P<start>{_MONTH_RE}\s*\d{{4}}|\d{{4}})\s*[-–—]\s*(?P<end>{_DATE_TOKEN_RE}|{_END_MARKERS_RE})\s*$",
    re.IGNORECASE,
)
# A line that ENDS with a date range after some other text - real-world
# CV templates commonly put "Job Title ... Févr. - Juin 2026" all on one
# line (title and dates sharing a row, dates often right-aligned) rather
# than the "title\ndates" two-line shape this module's other fixtures
# use. The start token also accepts a bare month with no year ("Févr.")
# since French CVs commonly omit a repeated year when both dates fall in
# the same year ("Juin - Août 2025").
_TRAILING_DATE_RANGE_RE = re.compile(
    rf"^(?P<prefix>.*?)\s+(?P<start>{_DATE_TOKEN_RE})\s*[-–—]\s*"
    rf"(?P<end>{_DATE_TOKEN_RE}|{_END_MARKERS_RE})\s*$",
    re.IGNORECASE,
)
# Bilingual "this is still ongoing" markers - matched against the end
# date only (see _is_current_marker), never the start date, after
# accent/case/punctuation folding so "Présent", "présent" and "present"
# all match the one entry below.
_CURRENT_MARKERS = frozenset(
    {"present", "current", "actuel", "actuelle", "aujourdhui", "en cours", "a ce jour"}
)

# A project header line ends with a trailing, comma-separated "(Tech,
# Tech, Tech)" list right after the project name - "Wassy -- Marketplace
# Multi-Services (React, React Native, Node.js, Express, MongoDB, JWT)".
# The comma requirement is what tells a real tech list apart from a
# plain clarifying aside like "(notions)" or "(Spring)". Projects have
# no dates to anchor on the way Experience entries do (see
# _TRAILING_DATE_RANGE_RE), so this is the equivalent boundary signal
# for a CV template that lists projects back-to-back with no blank line
# between them (confirmed on a real CV: nine projects with zero
# separation previously collapsed into one unusable block).
_PROJECT_HEADER_RE = re.compile(r"^(?P<name>.+?)\s*\((?P<technologies>[^()]*,[^()]*)\)\s*$")


def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.strip().lower())
    stripped = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9 ]", "", stripped)


def _is_current_marker(text: str | None) -> bool:
    return bool(text) and _fold(text) in _CURRENT_MARKERS


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
            for block in _split_entries(section.body_text)
            if (experience := _parse_experience_block(document_id, section, block)) is not None
        ]

        education = [
            entry
            for section in by_type.get(SectionType.EDUCATION, [])
            for block in _split_entries(section.body_text)
            if (entry := _parse_education_block(document_id, section, block)) is not None
        ]

        projects = [
            project
            for section in by_type.get(SectionType.PROJECTS, [])
            for block in _split_project_entries(section.body_text)
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


def _split_entries(body_text: str) -> list[str]:
    """Splits a section's body into one chunk per CV entry.

    A blank line is the primary boundary signal (`_split_blocks`), but
    some real-world CV templates lay entries out with no vertical gap
    between them at all - each entry's header line ("Job Title ... Févr.
    - Juin 2026") is visually distinguishable by ending in a date range,
    not by whitespace. When a blank-line block itself contains more than
    one such header line, it is further split at each one - this is what
    lets four back-to-back Experience entries with zero blank lines
    between them (confirmed on a real CV) still come out as four
    separate entries instead of one merged block with no usable title/
    date structure.
    """
    chunks: list[str] = []
    for block in _split_blocks(body_text):
        lines = block.split("\n")
        starts = [0]
        for index in range(1, len(lines)):
            extracted = _extract_date_range(lines[index])
            if extracted is not None and extracted[0]:
                starts.append(index)
        if len(starts) == 1:
            chunks.append(block)
            continue
        for start, end in zip(starts, [*starts[1:], len(lines)], strict=True):
            chunk = "\n".join(lines[start:end]).strip()
            if chunk:
                chunks.append(chunk)
    return chunks


def _split_project_entries(body_text: str) -> list[str]:
    """Mirrors `_split_entries` for the Projects section: a project
    header is identified by a trailing "(Tech, Tech, ...)" list
    (`_PROJECT_HEADER_RE`) rather than a date range, since projects don't
    carry dates. Without this, a template that lists every project
    back-to-back with no blank line between entries collapses the whole
    section into a single block with no usable per-project structure.
    """
    chunks: list[str] = []
    for block in _split_blocks(body_text):
        lines = block.split("\n")
        starts = [0]
        for index in range(1, len(lines)):
            if _PROJECT_HEADER_RE.match(lines[index].strip()):
                starts.append(index)
        if len(starts) == 1:
            chunks.append(block)
            continue
        for start, end in zip(starts, [*starts[1:], len(lines)], strict=True):
            chunk = "\n".join(lines[start:end]).strip()
            if chunk:
                chunks.append(chunk)
    return chunks


def _split_title_company(header: str) -> tuple[str | None, str | None]:
    # " chez " is French for " at " (e.g. "Ingenieure chez Meridian
    # Analytics") - checked before the more generic ", "/" - " separators
    # so it wins the way " at " already does for English.
    for separator in (" at ", " chez ", " | ", " - ", ", "):
        if separator in header:
            title, company = header.split(separator, 1)
            return title.strip() or None, company.strip() or None
    return header.strip() or None, None


def _split_date_range(line: str) -> tuple[str, str] | None:
    match = _DATE_RANGE_RE.match(line.strip())
    if not match:
        return None
    return match.group("start").strip(), match.group("end").strip()


def _extract_date_range(line: str) -> tuple[str, str, str] | None:
    """Finds a date range in `line`, returning (prefix, start, end).
    `prefix` is "" when the whole line is just the date range (checked
    first, via the stricter fully-anchored `_DATE_RANGE_RE`) - checking
    that case first matters: "January 2020 - Present" must never be
    parsed by the looser trailing-date pattern as prefix="January",
    start="2020", since "January" alone also happens to satisfy that
    pattern's bare-month start token.
    """
    stripped = line.strip()
    if match := _DATE_RANGE_RE.match(stripped):
        return "", match.group("start").strip(), match.group("end").strip()
    if match := _TRAILING_DATE_RANGE_RE.match(stripped):
        return match.group("prefix").strip(), match.group("start").strip(), match.group("end").strip()
    return None


def _looks_like_location(line: str) -> bool:
    """A location line is short, comma-shaped ("San Francisco, CA",
    "Paris, France"), and doesn't look like a description sentence or a
    "Technologies:" line - digits disqualify it since a real location
    almost never contains one (unlike a date range or a metric-laden
    achievement bullet)."""
    stripped = line.strip()
    if not stripped or len(stripped) > 60 or "," not in stripped:
        return False
    if any(char.isdigit() for char in stripped):
        return False
    if stripped.lower().startswith("technologies"):
        return False
    return True


def _parse_experience_block(
    document_id: str, section: DetectedSection, block: str
) -> Experience | None:
    lines = [line.strip() for line in block.split("\n") if line.strip()]
    if not lines:
        return None

    header = lines[0]
    remaining = lines[1:]
    start_date = end_date = None

    # Some real-world templates put the date range on the same line as
    # the title (often right-aligned) rather than on its own line below -
    # try that first, falling back to the "date on the next line" shape
    # every synthetic fixture in this repo uses.
    if (header_dates := _extract_date_range(header)) is not None and header_dates[0]:
        header, start_date, end_date = header_dates
    elif remaining and (dates := _split_date_range(remaining[0])):
        start_date, end_date = dates
        remaining = remaining[1:]

    title, company = _split_title_company(header)

    location = None
    # When the date lived on the header line (company never on that line
    # to begin with), the very next line is commonly "Company, City"
    # rather than a location on its own - split it instead of letting
    # _looks_like_location swallow the whole thing as a bare location and
    # silently drop the company name.
    if company is None and remaining and _looks_like_location(remaining[0]):
        company, _, location_part = remaining[0].partition(",")
        company = company.strip() or None
        location = location_part.strip() or None
        remaining = remaining[1:]
    elif remaining and _looks_like_location(remaining[0]):
        location = remaining[0].strip()
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
        location=location,
        is_current=_is_current_marker(end_date),
    )


def _parse_education_block(
    document_id: str, section: DetectedSection, block: str
) -> Education | None:
    lines = [line.strip() for line in block.split("\n") if line.strip()]
    if not lines:
        return None

    header = lines[0]
    remaining = lines[1:]
    start_date = end_date = None

    if (header_dates := _extract_date_range(header)) is not None and header_dates[0]:
        header, start_date, end_date = header_dates
    elif remaining and (dates := _split_date_range(remaining[0])):
        start_date, end_date = dates
        remaining = remaining[1:]

    degree, institution = _split_title_company(header)

    location = None
    if remaining and _looks_like_location(remaining[0]):
        location = remaining[0].strip()

    return Education(
        institution=institution,
        degree=degree,
        field_of_study=None,
        start_date_raw=start_date,
        end_date_raw=end_date,
        evidence=_section_evidence(document_id, section, block),
        location=location,
    )


def _parse_project_block(document_id: str, section: DetectedSection, block: str) -> Project | None:
    lines = [line.strip() for line in block.split("\n") if line.strip()]
    if not lines:
        return None

    name = lines[0]
    technologies: list[str] = []
    # A title ending in "(Tech, Tech, ...)" (the same signal
    # _split_project_entries splits on) doubles as the technology list
    # when there is no separate explicit "Technologies:" line - real CVs
    # commonly declare a project's stack this way instead.
    header_match = _PROJECT_HEADER_RE.match(name)
    if header_match:
        name = header_match.group("name").strip()
        technologies = split_delimited_tokens(header_match.group("technologies"))

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
