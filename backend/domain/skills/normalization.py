"""Skill name normalization.

Only maps names that are explicit surface forms of the SAME skill (see
section 19 of the Phase 2 brief): "JS" / "Javascript" / "ECMAScript" all
normalize to "JavaScript" because they are exactly the same technology
under different names.

This module deliberately does NOT infer relationships. "Django" is
related to "Python" (see Skill.parent_skill in domain/skills/entities.py)
but Django is not Python, and normalizing "Django" mentions to "Python"
would destroy information a future matching engine needs. If a raw name
isn't a known alias or canonical name, it does not get force-matched to
something plausible-looking - the caller keeps it as an unmatched raw
skill (see infrastructure/document_processing/extraction/candidate_extractor.py).
"""
import re
from collections.abc import Iterable, Mapping

from domain.skills.entities import Skill


def build_alias_index(skills: Iterable[Skill]) -> dict[str, Skill]:
    """Builds a lookup keyed by normalized alias/canonical-name text.

    A conflict (two skills claiming the same alias) keeps whichever skill
    was added first - callers control precedence by ordering `skills`.
    """
    index: dict[str, Skill] = {}
    for skill in skills:
        for name in (skill.canonical_name, *skill.aliases):
            key = _normalize_key(name)
            index.setdefault(key, skill)
    return index


def normalize_skill_name(raw_name: str, alias_index: Mapping[str, Skill]) -> Skill | None:
    """Returns the matching canonical Skill, or None if `raw_name` is not
    a known alias. None is a legitimate, expected result - it means "keep
    this as a raw, uncategorized skill mention" (see section 18/19).
    """
    key = _normalize_key(raw_name)
    if not key:
        return None
    return alias_index.get(key)


def _normalize_key(name: str) -> str:
    """Case/punctuation-insensitive key. Keeps `+`, `#`, and `.` since
    they are meaningful in names like "C++", "C#", "Node.js".
    """
    lowered = name.strip().lower()
    return re.sub(r"[^a-z0-9+#.]", "", lowered)
