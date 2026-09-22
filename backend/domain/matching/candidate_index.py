"""Flattens a CandidateProfile's skill evidence into one lookup keyed by
canonical skill name, so every matcher that needs "does the candidate
have skill X, and where" (skill matching, domain alignment) builds it
once instead of re-scanning `profile.skills`/`profile.experiences`
independently.
"""
from collections.abc import Mapping
from dataclasses import dataclass

from domain.cv.entities import CandidateProfile
from domain.documents.evidence import Evidence


@dataclass(frozen=True)
class CandidateSkillSignal:
    canonical_name: str
    source_type: str
    evidence: Evidence | None
    source_label: str | None
    raw_text: str | None


def build_candidate_skill_index(profile: CandidateProfile) -> dict[str, list[CandidateSkillSignal]]:
    index: dict[str, list[CandidateSkillSignal]] = {}

    for mention in profile.skills:
        if mention.skill is None:
            continue
        index.setdefault(mention.skill.canonical_name, []).append(
            CandidateSkillSignal(
                canonical_name=mention.skill.canonical_name,
                source_type="SKILL_SECTION",
                evidence=mention.evidence,
                source_label=None,
                raw_text=mention.raw_text,
            )
        )

    for experience in profile.experiences:
        label = _experience_label(experience)
        for technology_name in experience.technologies:
            index.setdefault(technology_name, []).append(
                CandidateSkillSignal(
                    canonical_name=technology_name,
                    source_type="EXPERIENCE",
                    evidence=experience.evidence,
                    source_label=label,
                    raw_text=None,
                )
            )

    for project in profile.projects:
        for technology_name in project.technologies:
            index.setdefault(technology_name, []).append(
                CandidateSkillSignal(
                    canonical_name=technology_name,
                    source_type="PROJECT",
                    evidence=project.evidence,
                    source_label=project.name,
                    raw_text=None,
                )
            )

    return index


def is_alias_surface_form(raw_text: str | None, canonical_name: str) -> bool:
    """True when `raw_text` is a different spelling than the canonical
    name it resolved to - the signal that an alias (not the canonical
    term itself) was what appeared in the source text.
    """
    if raw_text is None:
        return False
    return raw_text.strip().lower() != canonical_name.strip().lower()


def _experience_label(experience) -> str:
    parts = [part for part in (experience.title, experience.company) if part]
    return " at ".join(parts) if parts else "Experience"


def index_has_skill(index: Mapping[str, list[CandidateSkillSignal]], canonical_name: str) -> bool:
    return bool(index.get(canonical_name))
