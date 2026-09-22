"""Semantic enrichment for a CandidateProfile (Phase 3 sections 13-17).

Runs after application/cv/extract_candidate_profile.py has already
persisted the Phase 2 CandidateProfile - this reads the same in-memory
domain object that use case just built (before it goes out of scope) and
computes purely derived facts from it: per-experience seniority and
technology mentions, per-education degree level, per-language canonical
name/proficiency. Every value here is a deterministic function of a
field Phase 2 already extracted and evidenced; nothing here invents new
facts or attaches new evidence of its own.

    repository needs: apply_experience_enrichment(document_id, updates)
                       apply_education_enrichment(document_id, updates)
                       apply_language_enrichment(document_id, updates)
"""
from domain.cv.education_normalization import normalize_education_level
from domain.cv.entities import CandidateProfile
from domain.cv.language_normalization import normalize_language_name, normalize_proficiency
from domain.cv.seniority import normalize_seniority
from domain.skills.enrichment import TechnologyMentionScanner


class EnrichCandidateProfile:
    def __init__(self, repository) -> None:
        self._repository = repository

    def execute(self, document_id: str, profile: CandidateProfile, scanner: TechnologyMentionScanner) -> None:
        experience_updates = [
            {
                "seniority": normalize_seniority(experience.title).value,
                "technologies": _merge_technologies(experience, scanner),
            }
            for experience in profile.experiences
        ]
        if experience_updates:
            self._repository.apply_experience_enrichment(document_id, experience_updates)

        education_updates = [
            {"degree_level": normalize_education_level(education.degree).value}
            for education in profile.education
        ]
        if education_updates:
            self._repository.apply_education_enrichment(document_id, education_updates)

        language_updates = [
            {
                "canonical_name": normalize_language_name(language.name),
                "proficiency_normalized": normalize_proficiency(language.proficiency).value,
            }
            for language in profile.languages
        ]
        if language_updates:
            self._repository.apply_language_enrichment(document_id, language_updates)


def _merge_technologies(experience, scanner: TechnologyMentionScanner) -> list[str]:
    text = " ".join(filter(None, [experience.description, *experience.achievements]))
    mentioned = [skill.canonical_name for skill in scanner.scan(text)]
    # Union, preserving the explicit "Technologies:" list Phase 2 already
    # read (if any) before the prose-derived mentions, de-duplicated.
    return list(dict.fromkeys([*experience.technologies, *mentioned]))
