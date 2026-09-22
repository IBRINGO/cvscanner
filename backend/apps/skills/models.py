"""Persistence models for the skills app: the canonical skill taxonomy.

Seeded from domain/skills/taxonomy.py via a data migration (see
apps/skills/migrations/0002_seed_skill_taxonomy.py) so the same list
drives both the DB and framework-free unit tests. Designed to grow: add
entries to the taxonomy and write a new migration - see section 18 of
the Phase 2 brief.
"""
from django.db import models

from domain.skills.enums import SkillCategory


class Skill(models.Model):
    canonical_name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=32, choices=[(c.value, c.value) for c in SkillCategory])
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children"
    )
    related_skills = models.ManyToManyField("self", blank=True, symmetrical=True)

    class Meta:
        ordering = ["canonical_name"]

    def __str__(self) -> str:  # pragma: no cover
        return self.canonical_name


class SkillAlias(models.Model):
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="aliases")
    alias = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:  # pragma: no cover
        return self.alias
