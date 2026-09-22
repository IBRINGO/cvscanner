"""Semantic enrichment for a JobProfile (Phase 3 sections 15, 18-20).

Mirrors enrich_candidate_profile.py's approach: runs after Phase 2's
JobProfile has already been persisted, derives values purely from fields
Phase 2 already extracted, and never compares anything to a candidate
(section 19: this stays a classification of the requirement itself, not
a match).

    repository needs: apply_seniority(document_id, seniority_normalized)
                       apply_requirement_enrichment(document_id, updates)
"""
from domain.cv.education_normalization import EducationLevel, normalize_education_level
from domain.cv.seniority import normalize_seniority
from domain.job.entities import JobProfile
from domain.job.enums import RequirementType
from domain.job.requirement_semantics import parse_experience_requirement
from domain.skills.enrichment import TechnologyMentionScanner


class EnrichJobProfile:
    def __init__(self, repository) -> None:
        self._repository = repository

    def execute(self, document_id: str, profile: JobProfile, scanner: TechnologyMentionScanner) -> None:
        seniority = normalize_seniority(profile.seniority or profile.title)
        self._repository.apply_seniority(document_id, seniority.value)

        requirement_updates = [
            _enrich_requirement(requirement, scanner) for requirement in profile.requirements
        ]
        if requirement_updates:
            self._repository.apply_requirement_enrichment(document_id, requirement_updates)


def _enrich_requirement(requirement, scanner: TechnologyMentionScanner) -> dict:
    if requirement.requirement_type == RequirementType.EXPERIENCE:
        parsed = parse_experience_requirement(requirement.raw_text, scanner)
        return {
            "minimum_years": parsed.minimum_years,
            "normalized_value": parsed.technology.canonical_name if parsed.technology else None,
        }

    if requirement.requirement_type == RequirementType.EDUCATION:
        level = normalize_education_level(requirement.raw_text)
        return {"normalized_value": level.value if level != EducationLevel.UNKNOWN else None}

    return {}
