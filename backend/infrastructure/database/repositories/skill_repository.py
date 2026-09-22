"""Django ORM-backed SkillRepository.

Builds the alias -> Skill lookup extractors use for normalization
(domain.skills.normalization) from whatever is currently in the
database - so growing the taxonomy (section 18) is just adding rows via
a migration or the admin, with no code change required here.
"""
from apps.skills.models import Skill as DjangoSkill
from domain.skills.entities import Skill, SkillRelation
from domain.skills.enums import SkillCategory, SkillRelationType
from domain.skills.normalization import build_alias_index


class DjangoSkillRepository:
    def alias_index(self) -> dict[str, Skill]:
        return build_alias_index(self.all())

    def all(self) -> list[Skill]:
        rows = (
            DjangoSkill.objects.select_related("parent")
            .prefetch_related("aliases", "relations_from__to_skill")
        )
        return [self._to_entity(row) for row in rows]

    def get_by_name(self, canonical_name: str) -> Skill | None:
        row = (
            DjangoSkill.objects.select_related("parent")
            .prefetch_related("aliases", "relations_from__to_skill")
            .filter(canonical_name=canonical_name)
            .first()
        )
        return self._to_entity(row) if row else None

    def _to_entity(self, row: DjangoSkill) -> Skill:
        return Skill(
            canonical_name=row.canonical_name,
            category=SkillCategory(row.category),
            aliases=tuple(row.aliases.values_list("alias", flat=True)),
            parent_skill=row.parent.canonical_name if row.parent else None,
            ecosystem=row.ecosystem,
            description=row.description,
            relations=tuple(
                SkillRelation(
                    target_skill=relation.to_skill.canonical_name,
                    relation_type=SkillRelationType(relation.relation_type),
                )
                for relation in row.relations_from.all()
            ),
        )
