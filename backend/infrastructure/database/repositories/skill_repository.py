"""Django ORM-backed SkillRepository.

Builds the alias -> Skill lookup extractors use for normalization
(domain.skills.normalization) from whatever is currently in the
database - so growing the taxonomy (section 18) is just adding rows via
a migration or the admin, with no code change required here.
"""
from apps.skills.models import Skill as DjangoSkill
from domain.skills.entities import Skill
from domain.skills.enums import SkillCategory
from domain.skills.normalization import build_alias_index


class DjangoSkillRepository:
    def alias_index(self) -> dict[str, Skill]:
        rows = DjangoSkill.objects.select_related("parent").prefetch_related("aliases", "related_skills")
        skills = [self._to_entity(row) for row in rows]
        return build_alias_index(skills)

    def _to_entity(self, row: DjangoSkill) -> Skill:
        return Skill(
            canonical_name=row.canonical_name,
            category=SkillCategory(row.category),
            aliases=tuple(row.aliases.values_list("alias", flat=True)),
            parent_skill=row.parent.canonical_name if row.parent else None,
            related_skills=tuple(row.related_skills.values_list("canonical_name", flat=True)),
        )
