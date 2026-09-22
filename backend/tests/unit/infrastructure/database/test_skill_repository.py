import pytest

from domain.skills.enums import SkillRelationType
from infrastructure.database.repositories.skill_repository import DjangoSkillRepository

pytestmark = pytest.mark.django_db


class TestDjangoSkillRepository:
    def test_all_returns_seeded_taxonomy_with_ecosystem_and_description(self):
        skills = DjangoSkillRepository().all()
        django = next(s for s in skills if s.canonical_name == "Django")
        assert django.ecosystem == "Python ecosystem"
        assert django.description
        assert django.parent_skill == "Python"

    def test_explicit_relations_round_trip_from_the_database(self):
        django = DjangoSkillRepository().get_by_name("Django")
        alternatives = {
            relation.target_skill
            for relation in django.relations
            if relation.relation_type == SkillRelationType.ALTERNATIVE_TO
        }
        assert "Flask" in alternatives
        assert "FastAPI" in alternatives

    def test_get_by_name_returns_none_for_unknown_skill(self):
        assert DjangoSkillRepository().get_by_name("Nonexistent Skill") is None
