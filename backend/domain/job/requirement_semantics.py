"""Structured parsing of EXPERIENCE-type job requirements (Phase 3
sections 18-20).

Phase 2's RuleBasedJobExtractor already classifies a line like "3+ years
of experience with Python" as RequirementType.EXPERIENCE (see
infrastructure/document_processing/extraction/job_extractor.py) but keeps
only `raw_text`. This module extracts `minimum_years` and, where a known
skill is named in the same sentence, `technology` - without ever
comparing against a candidate. If the text does not contain an
unambiguous number, `minimum_years` stays None; the raw text is always
preserved either way.
"""
import re
from collections.abc import Mapping
from dataclasses import dataclass

from domain.skills.enrichment import TechnologyMentionScanner
from domain.skills.entities import Skill

_YEARS_RE = re.compile(r"(\d+)\+?\s*(?:years?|yrs?)", re.IGNORECASE)


@dataclass(frozen=True)
class ExperienceRequirement:
    raw_text: str
    minimum_years: int | None
    technology: Skill | None


def parse_experience_requirement(
    raw_text: str, skills: Mapping[str, Skill] | TechnologyMentionScanner
) -> ExperienceRequirement:
    """`skills` accepts either a pre-built TechnologyMentionScanner (reuse
    across every requirement in a document - see that class's docstring
    on why building it once matters) or, for convenience in tests, a
    mapping whose values are Skill instances to scan for.
    """
    years_match = _YEARS_RE.search(raw_text)
    minimum_years = int(years_match.group(1)) if years_match else None

    scanner = skills if isinstance(skills, TechnologyMentionScanner) else TechnologyMentionScanner(
        list(dict.fromkeys(skills.values()))
    )
    mentions = scanner.scan(raw_text)
    technology = mentions[0] if mentions else None

    return ExperienceRequirement(raw_text=raw_text, minimum_years=minimum_years, technology=technology)
