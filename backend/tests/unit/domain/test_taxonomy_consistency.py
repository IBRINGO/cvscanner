"""Referential-integrity guards for the seed taxonomy (domain/skills/
taxonomy.py). These do not test business behavior - they exist to catch a
typo'd canonical name in `parent_skill` or `relations` before it becomes a
silent dead reference (domain/skills/relationships.py resolves unknown
names by simply dropping them, so a typo would otherwise fail silently).
"""
from domain.skills.taxonomy import SEED_SKILLS


class TestTaxonomyConsistency:
    def test_canonical_names_are_unique(self):
        names = [skill.canonical_name for skill in SEED_SKILLS]
        assert len(names) == len(set(names))

    def test_every_parent_skill_reference_resolves(self):
        names = {skill.canonical_name for skill in SEED_SKILLS}
        for skill in SEED_SKILLS:
            if skill.parent_skill:
                assert skill.parent_skill in names, f"{skill.canonical_name} has unknown parent"

    def test_every_relation_target_resolves(self):
        names = {skill.canonical_name for skill in SEED_SKILLS}
        for skill in SEED_SKILLS:
            for relation in skill.relations:
                assert relation.target_skill in names, (
                    f"{skill.canonical_name} has unknown relation target {relation.target_skill!r}"
                )

    def test_no_skill_relates_to_itself(self):
        for skill in SEED_SKILLS:
            assert skill.parent_skill != skill.canonical_name
            for relation in skill.relations:
                assert relation.target_skill != skill.canonical_name

    def test_aliases_are_not_shared_across_different_skills(self):
        # A skill listing its own canonical name among its aliases is
        # harmless (build_alias_index just no-ops on it); only two
        # *different* skills claiming the same alias is a real conflict.
        seen: dict[str, str] = {}
        for skill in SEED_SKILLS:
            for name in (skill.canonical_name, *skill.aliases):
                key = name.strip().lower()
                owner = seen.setdefault(key, skill.canonical_name)
                message = f"{name!r} claimed by both {owner} and {skill.canonical_name}"
                assert owner == skill.canonical_name, message
