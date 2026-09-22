from domain.skills.entities import Skill, SkillRelation
from domain.skills.enums import SkillCategory, SkillRelationType
from domain.skills.relationships import build_relationship_view
from domain.skills.taxonomy import SEED_SKILLS


class TestBuildRelationshipView:
    def test_parent_is_derived_not_stored(self):
        django = next(s for s in SEED_SKILLS if s.canonical_name == "Django")
        view = build_relationship_view(django, SEED_SKILLS)
        assert view.parent.canonical_name == "Python"

    def test_children_are_derived_by_reverse_lookup(self):
        python = next(s for s in SEED_SKILLS if s.canonical_name == "Python")
        view = build_relationship_view(python, SEED_SKILLS)
        child_names = {child.canonical_name for child in view.children}
        assert "Django" in child_names
        assert "Flask" in child_names
        # A framework built on Python is never equated with Python.
        assert "Python" not in child_names

    def test_ecosystem_siblings_exclude_self(self):
        django = next(s for s in SEED_SKILLS if s.canonical_name == "Django")
        view = build_relationship_view(django, SEED_SKILLS)
        sibling_names = {sibling.canonical_name for sibling in view.ecosystem_siblings}
        assert "Flask" in sibling_names
        assert "Django" not in sibling_names

    def test_no_ecosystem_yields_no_siblings(self):
        rust = next(s for s in SEED_SKILLS if s.canonical_name == "Rust")
        view = build_relationship_view(rust, SEED_SKILLS)
        assert view.ecosystem_siblings == ()

    def test_explicit_relations_are_resolved_to_real_skills(self):
        django = next(s for s in SEED_SKILLS if s.canonical_name == "Django")
        view = build_relationship_view(django, SEED_SKILLS)
        alternative_type = SkillRelationType.ALTERNATIVE_TO
        alternatives = {
            r.skill.canonical_name for r in view.explicit if r.relation_type == alternative_type
        }
        assert "Flask" in alternatives
        assert "FastAPI" in alternatives

    def test_unresolvable_relation_target_is_silently_dropped(self):
        ghost = Skill(
            "Ghost",
            SkillCategory.TOOL,
            relations=(SkillRelation("Nonexistent Skill", SkillRelationType.RELATED_TO),),
        )
        view = build_relationship_view(ghost, (ghost,))
        assert view.explicit == ()

    def test_all_related_combines_every_derivation(self):
        django = next(s for s in SEED_SKILLS if s.canonical_name == "Django")
        view = build_relationship_view(django, SEED_SKILLS)
        all_related_names = {r.skill.canonical_name for r in view.all_related}
        assert "Python" in all_related_names  # parent -> CHILD_OF
        assert "Django REST Framework" in all_related_names  # child -> PARENT_OF
        assert "Flask" in all_related_names  # ecosystem sibling and explicit alternative

    def test_relationship_never_implies_equivalence(self):
        # Section 12: relationships can exist without identity.
        django = next(s for s in SEED_SKILLS if s.canonical_name == "Django")
        python = next(s for s in SEED_SKILLS if s.canonical_name == "Python")
        view = build_relationship_view(django, SEED_SKILLS)
        assert view.parent.canonical_name == python.canonical_name
        assert django.canonical_name != python.canonical_name
