"""Scans free text (an experience description, a project blurb, ...) for
mentions of known skills (Phase 3 section 13).

Phase 2 only reads skills from a dedicated Skills section (see
docs/architecture/phase-2-pipeline.md "Known limitations"). This module
is the Phase 3 enrichment that additionally recognizes skills mentioned
inside prose - "Built REST APIs using Django and PostgreSQL" yields
Django and PostgreSQL as technology mentions on that experience - without
touching how the Skills section itself is read.

Deterministic, alias-based matching only (method TAXONOMY - see
domain/documents/enums.py::ExtractionMethod): no inference, no fuzzy
matching. A skill not present in the taxonomy is simply not found; this
module never invents or guesses a skill from context.
"""
import re
from collections.abc import Sequence

from domain.skills.entities import Skill


class TechnologyMentionScanner:
    """Built once per document (or per batch) from the full skill list,
    then reused across every experience/project text on that document -
    building the alternation pattern is the only non-trivial cost, and
    section 66 asks not to repeat it unnecessarily.
    """

    def __init__(self, skills: Sequence[Skill]) -> None:
        surface_forms: list[tuple[str, Skill]] = []
        for skill in skills:
            surface_forms.append((skill.canonical_name, skill))
            surface_forms.extend((alias, skill) for alias in skill.aliases)

        # Longest surface form first, so "Django REST Framework" matches
        # before the shorter "Django" would otherwise consume the text.
        surface_forms.sort(key=lambda pair: len(pair[0]), reverse=True)

        self._skill_by_form: dict[str, Skill] = {}
        pattern_parts: list[str] = []
        for form, skill in surface_forms:
            key = form.lower()
            if key in self._skill_by_form:
                continue
            self._skill_by_form[key] = skill
            pattern_parts.append(re.escape(form))

        if pattern_parts:
            alternation = "|".join(pattern_parts)
            # Custom boundaries (not \b) because surface forms like "C++",
            # "C#", and ".NET" contain non-word characters that \b handles
            # inconsistently at a trailing punctuation/space transition.
            self._pattern = re.compile(
                rf"(?<![A-Za-z0-9])(?:{alternation})(?![A-Za-z0-9])", re.IGNORECASE
            )
        else:
            self._pattern = None

    def scan(self, text: str) -> list[Skill]:
        """Returns the distinct skills mentioned in `text`, in first-seen
        order. Empty/blank text always yields an empty list.
        """
        if not text or self._pattern is None:
            return []

        seen: dict[str, Skill] = {}
        for match in self._pattern.finditer(text):
            skill = self._skill_by_form[match.group(0).lower()]
            seen.setdefault(skill.canonical_name, skill)
        return list(seen.values())
