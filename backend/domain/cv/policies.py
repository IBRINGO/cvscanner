"""Rule-based section detection (section 13 of the Phase 2 brief).

A deterministic first version: normalize known heading strings to a
canonical SectionType, then split a parsed document into sections at
lines that look like headings. This is intentionally simple - the brief
explicitly asks for a rule-based v1, not an ML classifier, while keeping
the architecture (SectionType is just an enum; detect_sections just
returns a list) able to support a smarter classifier later without
changing any caller.

Shared by CV and job-offer parsing (see domain/job/ use cases) since both
document types have headings that need the same normalization step.
"""
import re

from domain.documents.entities import DetectedSection, ParsedDocument
from domain.documents.enums import SectionType

# Lowercase, punctuation-stripped alias -> canonical SectionType. Order
# does not matter; lookup is by exact normalized match first, then a
# substring pass (see normalize_section_heading).
SECTION_ALIASES: dict[SectionType, frozenset[str]] = {
    SectionType.SUMMARY: frozenset({"summary", "profile", "objective", "about", "professional summary"}),
    SectionType.EXPERIENCE: frozenset(
        {
            "experience",
            "professional experience",
            "work experience",
            "employment history",
            "career history",
        }
    ),
    SectionType.EDUCATION: frozenset({"education", "academic background", "qualifications"}),
    SectionType.SKILLS: frozenset(
        {"skills", "technical skills", "core competencies", "competencies"}
    ),
    SectionType.PROJECTS: frozenset({"projects", "personal projects", "key projects"}),
    SectionType.CERTIFICATIONS: frozenset(
        {"certifications", "certificates", "licenses", "licenses and certifications"}
    ),
    SectionType.LANGUAGES: frozenset({"languages"}),
    SectionType.ACHIEVEMENTS: frozenset({"achievements", "awards", "honors"}),
    SectionType.PUBLICATIONS: frozenset({"publications"}),
    SectionType.VOLUNTEER_EXPERIENCE: frozenset({"volunteer experience", "volunteering"}),
    SectionType.RESPONSIBILITIES: frozenset(
        {"responsibilities", "what you'll do", "the role", "role"}
    ),
    SectionType.REQUIREMENTS: frozenset(
        {
            "requirements",
            "qualifications",
            "what we're looking for",
            "required skills",
            "must have",
        }
    ),
}

_MAX_HEADING_LENGTH = 45
_HEADING_LOOKUP: dict[str, SectionType] = {
    alias: section_type for section_type, aliases in SECTION_ALIASES.items() for alias in aliases
}


def normalize_section_heading(raw_heading: str) -> SectionType:
    """Maps a raw heading string (e.g. "Professional Experience") to a
    canonical SectionType. Falls back to OTHER rather than guessing.
    """
    cleaned = _clean(raw_heading)
    if cleaned in _HEADING_LOOKUP:
        return _HEADING_LOOKUP[cleaned]

    # Substring pass: "professional experience section" still matches
    # "experience". Longer aliases are checked first so "work experience"
    # wins over a shorter coincidental match.
    for alias in sorted(_HEADING_LOOKUP, key=len, reverse=True):
        if alias in cleaned:
            return _HEADING_LOOKUP[alias]

    return SectionType.OTHER


def _clean(text: str) -> str:
    return re.sub(r"[^a-z0-9' ]", "", text.strip().lower()).strip()


def _looks_like_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped or len(stripped) > _MAX_HEADING_LENGTH:
        return False
    if stripped.endswith((".", ",", ";")):
        return False
    # `len(stripped) >= 5` keeps short all-caps acronyms that are really
    # just skill tokens (AWS, SQL, GCP, CSS) from being misread as a new
    # section heading - every real heading this module recognizes is at
    # least 5 characters long ("SKILLS" is the shortest).
    if stripped.isupper() and len(stripped.split()) <= 6 and len(stripped) >= 5:
        return True

    cleaned = _clean(stripped)
    if cleaned in _HEADING_LOOKUP:
        return True

    # The substring fallback below only fires for short, heading-shaped
    # lines. Without this gate, a sentence that merely mentions a keyword
    # (e.g. "5+ years of experience", "familiar with core competencies")
    # would be misclassified as a section heading just because "experience"
    # or "competencies" appears in it.
    if len(cleaned.split()) > 3:
        return False
    return normalize_section_heading(stripped) != SectionType.OTHER


def detect_sections(parsed: ParsedDocument) -> list[DetectedSection]:
    """Splits a parsed document into sections at heading-like lines.

    Text before the first detected heading is not discarded - it is
    returned as a leading SectionType.OTHER section (typically the name/
    contact block at the top of a CV, or the job title block at the top
    of a job offer).
    """
    lines_with_pages = _flatten_lines(parsed)
    if not lines_with_pages:
        return []

    sections: list[DetectedSection] = []
    current_type = SectionType.OTHER
    current_heading = ""
    current_page: int | None = lines_with_pages[0][0]
    current_lines: list[str] = []

    def flush() -> None:
        body = "\n".join(current_lines).strip()
        if body or current_heading:
            sections.append(
                DetectedSection(
                    section_type=current_type,
                    heading_text=current_heading,
                    body_text=body,
                    page_number=current_page,
                )
            )

    for page_number, line in lines_with_pages:
        if _looks_like_heading(line):
            flush()
            current_type = normalize_section_heading(line)
            current_heading = line.strip()
            current_page = page_number
            current_lines = []
        else:
            current_lines.append(line)

    flush()
    return sections


def _flatten_lines(parsed: ParsedDocument) -> list[tuple[int | None, str]]:
    """Line-by-line (page_number, line) pairs, preserving page boundaries
    when the parser provided them (PDF); page_number is None throughout
    for formats without page semantics (DOCX) - see
    domain/documents/entities.py's ParsedBlock docstring.

    Blank lines are kept (not filtered): they are the paragraph-boundary
    signal extractors use to split a section's body into separate entries
    (e.g. two Experience entries), via `body_text.split("\\n\\n")`.
    """
    if parsed.pages:
        result: list[tuple[int | None, str]] = []
        for page in parsed.pages:
            for line in page.text.splitlines():
                result.append((page.page_number, line))
        return result

    return [(None, line) for line in parsed.raw_text.splitlines()]
