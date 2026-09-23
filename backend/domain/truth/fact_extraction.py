"""Builds the Truth Layer's trusted fact set from an already-extracted
`CandidateProfile` (Phase 5 section 15). This is deliberately a pure
re-projection - it never re-parses the CV, never infers anything Phase
2/3 did not already establish, and never asks an LLM anything. The
Truth Layer's authority comes entirely from facts Phase 2/3 already
verified with Evidence.
"""
from domain.cv.entities import CandidateProfile
from domain.truth.entities import CandidateFact
from domain.truth.enums import AllowedTransformation, FactType, VerificationStatus

_SKILL_TRANSFORMATIONS = (AllowedTransformation.REORDER, AllowedTransformation.REPHRASE)
_EXPERIENCE_TRANSFORMATIONS = (
    AllowedTransformation.REORDER,
    AllowedTransformation.REPHRASE,
    AllowedTransformation.SUMMARIZE,
    AllowedTransformation.CONDENSE,
    AllowedTransformation.EXPAND_WITH_EXISTING_EVIDENCE,
)
_PROJECT_TRANSFORMATIONS = (
    AllowedTransformation.REORDER,
    AllowedTransformation.REPHRASE,
    AllowedTransformation.SUMMARIZE,
    AllowedTransformation.CONDENSE,
)
_EDUCATION_TRANSFORMATIONS = (AllowedTransformation.REORDER, AllowedTransformation.REPHRASE)
_CERTIFICATION_TRANSFORMATIONS = (AllowedTransformation.REORDER, AllowedTransformation.REPHRASE)
_LANGUAGE_TRANSFORMATIONS = (AllowedTransformation.REORDER,)


def _status_for_evidence(confidence: float | None) -> VerificationStatus:
    """A fact with a direct Evidence record (page/section/extraction
    method) is VERIFIED - it was read, not guessed. A fact present in the
    structured profile but without its own Evidence link is SUPPORTED:
    real, but not independently re-checkable against a source snippet.
    """
    return VerificationStatus.VERIFIED if confidence is not None else VerificationStatus.SUPPORTED


def build_candidate_facts(profile: CandidateProfile) -> tuple[CandidateFact, ...]:
    facts: list[CandidateFact] = []

    for index, mention in enumerate(profile.skills):
        confidence = mention.evidence.confidence if mention.evidence else None
        facts.append(
            CandidateFact(
                id=f"skill:{index}",
                type=FactType.SKILL,
                value=mention.raw_text,
                normalized_value=mention.skill.canonical_name if mention.skill else None,
                confidence=confidence if confidence is not None else 0.5,
                verification_status=_status_for_evidence(confidence),
                allowed_transformations=_SKILL_TRANSFORMATIONS,
                evidence=mention.evidence,
            )
        )

    for index, experience in enumerate(profile.experiences):
        confidence = experience.evidence.confidence if experience.evidence else None
        # `value` is the description only (not title/company) - that is
        # the one field tailoring ever rewrites, and the one field
        # domain/matching/responsibility_matching.py reads for lexical/
        # semantic overlap. Title and company are the experience's
        # identity, not content to rephrase.
        facts.append(
            CandidateFact(
                id=f"experience:{index}",
                type=FactType.EXPERIENCE,
                value=experience.description or "",
                normalized_value=None,
                confidence=confidence if confidence is not None else 0.5,
                verification_status=_status_for_evidence(confidence),
                allowed_transformations=_EXPERIENCE_TRANSFORMATIONS,
                evidence=experience.evidence,
            )
        )

    for index, project in enumerate(profile.projects):
        confidence = project.evidence.confidence if project.evidence else None
        facts.append(
            CandidateFact(
                id=f"project:{index}",
                type=FactType.PROJECT,
                value=project.name,
                normalized_value=None,
                confidence=confidence if confidence is not None else 0.5,
                verification_status=_status_for_evidence(confidence),
                allowed_transformations=_PROJECT_TRANSFORMATIONS,
                evidence=project.evidence,
            )
        )

    for index, education in enumerate(profile.education):
        confidence = education.evidence.confidence if education.evidence else None
        value = " - ".join(part for part in (education.degree, education.institution) if part)
        facts.append(
            CandidateFact(
                id=f"education:{index}",
                type=FactType.EDUCATION,
                value=value,
                normalized_value=education.degree_level.value if education.degree_level else None,
                confidence=confidence if confidence is not None else 0.5,
                verification_status=_status_for_evidence(confidence),
                allowed_transformations=_EDUCATION_TRANSFORMATIONS,
                evidence=education.evidence,
            )
        )

    for index, certification in enumerate(profile.certifications):
        confidence = certification.evidence.confidence if certification.evidence else None
        facts.append(
            CandidateFact(
                id=f"certification:{index}",
                type=FactType.CERTIFICATION,
                value=certification.name,
                normalized_value=None,
                confidence=confidence if confidence is not None else 0.5,
                verification_status=_status_for_evidence(confidence),
                allowed_transformations=_CERTIFICATION_TRANSFORMATIONS,
                evidence=certification.evidence,
            )
        )

    for index, language in enumerate(profile.languages):
        confidence = language.evidence.confidence if language.evidence else None
        facts.append(
            CandidateFact(
                id=f"language:{index}",
                type=FactType.LANGUAGE,
                value=language.name,
                normalized_value=(
                    language.proficiency_normalized.value if language.proficiency_normalized else None
                ),
                confidence=confidence if confidence is not None else 0.5,
                verification_status=_status_for_evidence(confidence),
                allowed_transformations=_LANGUAGE_TRANSFORMATIONS,
                evidence=language.evidence,
            )
        )

    return tuple(facts)
