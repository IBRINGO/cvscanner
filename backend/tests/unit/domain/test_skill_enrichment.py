from domain.skills.enrichment import TechnologyMentionScanner
from domain.skills.taxonomy import SEED_SKILLS


class TestTechnologyMentionScanner:
    def test_finds_multiple_distinct_skills_in_prose(self):
        scanner = TechnologyMentionScanner(SEED_SKILLS)
        text = "Built REST APIs using Django and PostgreSQL, deployed with Docker."
        found = {skill.canonical_name for skill in scanner.scan(text)}
        assert found == {"REST", "Django", "PostgreSQL", "Docker"}

    def test_does_not_equate_related_skills(self):
        # "Django" in prose must never surface "Python" as a mention -
        # Django != Python even though Django's parent_skill is Python.
        scanner = TechnologyMentionScanner(SEED_SKILLS)
        found = {skill.canonical_name for skill in scanner.scan("Developed services with Django.")}
        assert found == {"Django"}
        assert "Python" not in found

    def test_longest_surface_form_wins(self):
        scanner = TechnologyMentionScanner(SEED_SKILLS)
        found = {skill.canonical_name for skill in scanner.scan("Built APIs with Django REST Framework.")}
        assert "Django REST Framework" in found
        assert "Django" not in found

    def test_special_characters_in_surface_form_are_matched_correctly(self):
        scanner = TechnologyMentionScanner(SEED_SKILLS)
        found = {skill.canonical_name for skill in scanner.scan("Wrote services in C++ and C#.")}
        assert found == {"C++", "C#"}

    def test_case_insensitive_alias_matching(self):
        scanner = TechnologyMentionScanner(SEED_SKILLS)
        text = "Frontend built with REACTJS and typescript."
        found = {skill.canonical_name for skill in scanner.scan(text)}
        assert found == {"React", "TypeScript"}

    def test_no_false_positive_on_substring_of_unrelated_word(self):
        scanner = TechnologyMentionScanner(SEED_SKILLS)
        # "Go" is a real skill; "Gopher" or "going" must not match it.
        found = {skill.canonical_name for skill in scanner.scan("We are going to improve throughput.")}
        assert "Go" not in found

    def test_empty_text_returns_empty_list(self):
        scanner = TechnologyMentionScanner(SEED_SKILLS)
        assert scanner.scan("") == []
        assert scanner.scan(None) == []

    def test_duplicate_mentions_are_deduplicated(self):
        scanner = TechnologyMentionScanner(SEED_SKILLS)
        found = scanner.scan("Python, python, and more Python code.")
        assert len(found) == 1
        assert found[0].canonical_name == "Python"

    def test_empty_skill_list_never_matches_anything(self):
        scanner = TechnologyMentionScanner(())
        assert scanner.scan("Django and Python everywhere") == []
