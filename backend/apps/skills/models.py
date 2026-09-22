"""Persistence models for the skills app: the canonical skill taxonomy.

Seeded from domain/skills/taxonomy.py via a data migration (see
apps/skills/migrations/0002_seed_skill_taxonomy.py) so the same list
drives both the DB and framework-free unit tests. Designed to grow: add
entries to the taxonomy and write a new migration - see section 18 of
the Phase 2 brief.
"""
from django.db import models

from domain.skills.enums import SkillCategory, SkillRelationType


class Skill(models.Model):
    canonical_name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=32, choices=[(c.value, c.value) for c in SkillCategory])
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children"
    )
    ecosystem = models.CharField(max_length=100, null=True, blank=True)
    description = models.CharField(max_length=300, null=True, blank=True)

    class Meta:
        ordering = ["canonical_name"]

    def __str__(self) -> str:  # pragma: no cover
        return self.canonical_name


class SkillAlias(models.Model):
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="aliases")
    alias = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:  # pragma: no cover
        return self.alias


class SkillRelation(models.Model):
    """An explicit, typed, directional edge between two skills (Phase 3
    section 9). Only RELATED_TO / ALTERNATIVE_TO / BUILDS_ON are ever
    stored here - PARENT_OF / CHILD_OF / PART_OF_ECOSYSTEM are derived
    from `Skill.parent` / `Skill.ecosystem` at read time instead (see
    domain/skills/relationships.py), so they are never duplicated as rows.
    """

    from_skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="relations_from")
    to_skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="relations_to")
    relation_type = models.CharField(
        max_length=20, choices=[(t.value, t.value) for t in SkillRelationType]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["from_skill", "to_skill", "relation_type"], name="unique_skill_relation"
            )
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.from_skill_id} -{self.relation_type}-> {self.to_skill_id}"
