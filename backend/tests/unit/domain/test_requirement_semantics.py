from domain.job.requirement_semantics import parse_experience_requirement
from domain.skills.enrichment import TechnologyMentionScanner
from domain.skills.taxonomy import SEED_SKILLS


class TestParseExperienceRequirement:
    def test_extracts_minimum_years_and_technology(self):
        scanner = TechnologyMentionScanner(SEED_SKILLS)
        result = parse_experience_requirement("5 years of Java development", scanner)
        assert result.minimum_years == 5
        assert result.technology.canonical_name == "Java"
        assert result.raw_text == "5 years of Java development"

    def test_handles_plus_notation(self):
        scanner = TechnologyMentionScanner(SEED_SKILLS)
        result = parse_experience_requirement("3+ years of experience with Python", scanner)
        assert result.minimum_years == 3
        assert result.technology.canonical_name == "Python"

    def test_ambiguous_text_preserves_raw_text_without_inventing_years(self):
        scanner = TechnologyMentionScanner(SEED_SKILLS)
        result = parse_experience_requirement("Significant experience with Django", scanner)
        assert result.minimum_years is None
        assert result.technology.canonical_name == "Django"
        assert result.raw_text == "Significant experience with Django"

    def test_no_technology_named_leaves_technology_none(self):
        scanner = TechnologyMentionScanner(SEED_SKILLS)
        result = parse_experience_requirement("5 years in a similar role", scanner)
        assert result.minimum_years == 5
        assert result.technology is None
