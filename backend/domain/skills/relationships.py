"""Derives a skill's full relationship view for display (Phase 3 section
9-10).

PARENT_OF / CHILD_OF and PART_OF_ECOSYSTEM are computed here from
`Skill.parent_skill` / `Skill.ecosystem` rather than stored as duplicate
pairwise rows - section 8 of the brief: "Do not make all relationships
bidirectional manually if the data model can derive them." Only the
explicit, editorial relationships (RELATED_TO, ALTERNATIVE_TO, BUILDS_ON)
come from `Skill.relations`.

None of this ever asserts that two skills are the same thing. A relation
says two canonical skills are connected in a specific, named way - never
that a candidate or job that mentions one thereby mentions the other.
"""
from collections.abc import Sequence
from dataclasses import dataclass

from domain.skills.entities import Skill
from domain.skills.enums import SkillRelationType


@dataclass(frozen=True)
class RelatedSkill:
    skill: Skill
    relation_type: SkillRelationType


@dataclass(frozen=True)
class SkillRelationshipView:
    skill: Skill
    parent: Skill | None
    children: tuple[Skill, ...]
    ecosystem_siblings: tuple[Skill, ...]
    explicit: tuple[RelatedSkill, ...]

    @property
    def all_related(self) -> tuple[RelatedSkill, ...]:
        """Every related skill in one flat, typed list - convenient for a
        frontend that just wants to render "related skills" without
        caring which derivation produced each one.
        """
        related: list[RelatedSkill] = []
        if self.parent is not None:
            related.append(RelatedSkill(self.parent, SkillRelationType.CHILD_OF))
        related.extend(RelatedSkill(child, SkillRelationType.PARENT_OF) for child in self.children)
        related.extend(
            RelatedSkill(sibling, SkillRelationType.PART_OF_ECOSYSTEM)
            for sibling in self.ecosystem_siblings
        )
        related.extend(self.explicit)
        return tuple(related)


def build_relationship_view(skill: Skill, all_skills: Sequence[Skill]) -> SkillRelationshipView:
    by_name = {candidate.canonical_name: candidate for candidate in all_skills}

    parent = by_name.get(skill.parent_skill) if skill.parent_skill else None
    children = tuple(
        candidate for candidate in all_skills if candidate.parent_skill == skill.canonical_name
    )
    ecosystem_siblings = tuple(
        candidate
        for candidate in all_skills
        if skill.ecosystem
        and candidate.ecosystem == skill.ecosystem
        and candidate.canonical_name != skill.canonical_name
    )
    explicit = tuple(
        RelatedSkill(skill=by_name[relation.target_skill], relation_type=relation.relation_type)
        for relation in skill.relations
        if relation.target_skill in by_name
    )

    return SkillRelationshipView(
        skill=skill,
        parent=parent,
        children=children,
        ecosystem_siblings=ecosystem_siblings,
        explicit=explicit,
    )
