from dataclasses import dataclass, field

from domain.skills.enums import SkillCategory, SkillRelationType


@dataclass(frozen=True)
class SkillRelation:
    """One explicit, typed edge from a skill to another skill (Phase 3
    section 9). `target_skill` is a canonical name, not a nested Skill
    object - see the Skill docstring below for why.

    Only RELATED_TO / ALTERNATIVE_TO / BUILDS_ON ever appear here.
    PARENT_OF, CHILD_OF, and PART_OF_ECOSYSTEM are derived, not stored -
    see domain/skills/relationships.py.
    """

    target_skill: str
    relation_type: SkillRelationType


@dataclass(frozen=True)
class Skill:
    """A canonical skill and the surface forms that normalize to it.

    `parent_skill` holds a canonical name (string), not a nested Skill
    object, to keep this dataclass trivially constructible for the seed
    dataset and for tests - the repository layer resolves names to rows/
    objects when it needs to. Same for `relations[].target_skill`.

    Deliberately NOT modeled: "Django implies Python". A framework's
    parent is a *category* relationship for taxonomy browsing, not an
    equivalence - see domain/skills/normalization.py's module docstring.

    `ecosystem` groups skills that are commonly used together under one
    umbrella (e.g. "Python ecosystem") without asserting any one of them
    IS another - two skills sharing an ecosystem are PART_OF_ECOSYSTEM
    peers, derived automatically (see domain/skills/relationships.py),
    not stored as pairwise relations.
    """

    canonical_name: str
    category: SkillCategory
    aliases: tuple[str, ...] = field(default_factory=tuple)
    parent_skill: str | None = None
    ecosystem: str | None = None
    description: str | None = None
    relations: tuple[SkillRelation, ...] = field(default_factory=tuple)
