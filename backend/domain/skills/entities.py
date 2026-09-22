from dataclasses import dataclass, field

from domain.skills.enums import SkillCategory


@dataclass(frozen=True)
class Skill:
    """A canonical skill and the surface forms that normalize to it.

    `parent_skill` and `related_skills` hold canonical names (strings),
    not nested Skill objects, to keep this dataclass trivially
    constructible for the seed dataset and for tests - the repository
    layer resolves names to rows/objects when it needs to.

    Deliberately NOT modeled: "Django implies Python". A framework's
    parent is a *category* relationship for taxonomy browsing, not an
    equivalence - see domain/skills/normalization.py's module docstring.
    """

    canonical_name: str
    category: SkillCategory
    aliases: tuple[str, ...] = field(default_factory=tuple)
    parent_skill: str | None = None
    related_skills: tuple[str, ...] = field(default_factory=tuple)
