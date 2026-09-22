from domain.skills.entities import Skill
from domain.skills.enums import SkillCategory
from domain.skills.normalization import build_alias_index, normalize_skill_name
from domain.skills.taxonomy import SEED_SKILLS


class TestBuildAliasIndex:
    def test_canonical_name_and_aliases_are_all_indexed(self):
        skills = (Skill("JavaScript", SkillCategory.PROGRAMMING_LANGUAGE, aliases=("js", "ecmascript")),)
        index = build_alias_index(skills)
        assert index["javascript"].canonical_name == "JavaScript"
        assert index["js"].canonical_name == "JavaScript"
        assert index["ecmascript"].canonical_name == "JavaScript"


class TestNormalizeSkillName:
    def test_matches_alias_case_insensitively(self):
        index = build_alias_index(SEED_SKILLS)
        assert normalize_skill_name("javascript", index).canonical_name == "JavaScript"
        assert normalize_skill_name("JS", index).canonical_name == "JavaScript"
        assert normalize_skill_name("  Js  ", index).canonical_name == "JavaScript"

    def test_react_variants_normalize_to_react(self):
        index = build_alias_index(SEED_SKILLS)
        for variant in ("React", "react.js", "ReactJS", "reactjs"):
            assert normalize_skill_name(variant, index).canonical_name == "React"

    def test_unrecognized_skill_returns_none_rather_than_guessing(self):
        index = build_alias_index(SEED_SKILLS)
        assert normalize_skill_name("Some Obscure Internal Tool", index) is None

    def test_does_not_equate_a_framework_with_its_parent_language(self):
        # Django is related to Python but is not Python - normalizing
        # "Django" must never resolve to the Python skill.
        index = build_alias_index(SEED_SKILLS)
        django = normalize_skill_name("Django", index)
        python = normalize_skill_name("Python", index)
        assert django.canonical_name == "Django"
        assert python.canonical_name == "Python"
        assert django.canonical_name != python.canonical_name
        assert django.parent_skill == "Python"

    def test_empty_string_returns_none(self):
        index = build_alias_index(SEED_SKILLS)
        assert normalize_skill_name("", index) is None
        assert normalize_skill_name("   ", index) is None
