"""Deterministic claim validation (Phase 5 sections 18, 30, 72).

This is the independent safety net the brief insists on: "do not rely
solely on asking the LLM 'did you hallucinate?'" (section 18). Every
piece of text a tailoring step proposes is checked here, in plain
Python, against the Truth Layer's verified facts - regardless of what
the LLM (or a deterministic rewrite) claims about its own output.

Reuses `domain.skills.enrichment.TechnologyMentionScanner` (Phase 3) for
technology-mention detection and
`domain.cv.education_normalization.normalize_education_level` /
`domain.cv.language_normalization.normalize_proficiency` (Phase 3) for
education/language keyword detection, rather than inventing parallel
keyword tables that could quietly drift out of sync with the ones the
matching engine already trusts.
"""
import re
from dataclasses import dataclass, field

from domain.cv.education_normalization import EducationLevel, normalize_education_level
from domain.cv.language_normalization import LanguageProficiency
from domain.skills.enrichment import TechnologyMentionScanner
from domain.truth.enums import ClaimRejectionReason

# `domain.cv.language_normalization.normalize_proficiency` does an exact
# match on a short raw field value (a CV's own proficiency string), not a
# substring search over free-form prose - unsuitable for scanning a
# generated sentence. This mirrors the same proficiency vocabulary as
# language_normalization.py's `_PROFICIENCY_ALIASES` (kept in sync
# intentionally) but as word-boundary patterns, checked most-senior-first
# so "native speaker" resolves to NATIVE before a looser pattern could
# misfire.
_PROFICIENCY_KEYWORD_PATTERNS: tuple[tuple[LanguageProficiency, re.Pattern[str]], ...] = (
    (LanguageProficiency.NATIVE, re.compile(r"\b(native|mother tongue|bilingual)\b", re.IGNORECASE)),
    (LanguageProficiency.FLUENT, re.compile(r"\b(fluent|c2|full professional)\b", re.IGNORECASE)),
    (LanguageProficiency.ADVANCED, re.compile(r"\b(advanced|c1|professional working)\b", re.IGNORECASE)),
    (LanguageProficiency.UPPER_INTERMEDIATE, re.compile(r"\b(upper.intermediate|b2)\b", re.IGNORECASE)),
    (LanguageProficiency.INTERMEDIATE, re.compile(r"\b(intermediate|b1)\b", re.IGNORECASE)),
    (LanguageProficiency.ELEMENTARY, re.compile(r"\b(elementary|a2)\b", re.IGNORECASE)),
    (LanguageProficiency.BEGINNER, re.compile(r"\b(beginner|basic|a1)\b", re.IGNORECASE)),
)


def _detect_proficiency_claim(text: str) -> LanguageProficiency:
    for level, pattern in _PROFICIENCY_KEYWORD_PATTERNS:
        if pattern.search(text):
            return level
    return LanguageProficiency.UNKNOWN

# Mirrors the ladder domain/matching/education_matching.py and
# domain/matching/language_matching.py already use for comparison -
# duplicated here (rather than importing a private helper across module
# boundaries) because it is a small, stable, already-published ordering.
_EDUCATION_ORDER: tuple[EducationLevel, ...] = (
    EducationLevel.HIGH_SCHOOL,
    EducationLevel.ASSOCIATE,
    EducationLevel.BACHELOR,
    EducationLevel.MASTER,
    EducationLevel.DOCTORATE,
)
_PROFICIENCY_ORDER: tuple[LanguageProficiency, ...] = (
    LanguageProficiency.BEGINNER,
    LanguageProficiency.ELEMENTARY,
    LanguageProficiency.INTERMEDIATE,
    LanguageProficiency.UPPER_INTERMEDIATE,
    LanguageProficiency.ADVANCED,
    LanguageProficiency.FLUENT,
    LanguageProficiency.NATIVE,
)

_CERTIFICATION_PATTERN = re.compile(r"\b(certified|certification|certificate)\b", re.IGNORECASE)
_YEARS_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\+?\s*years?", re.IGNORECASE)
_DURATION_TOLERANCE_YEARS = 0.5


@dataclass(frozen=True)
class ClaimViolation:
    reason: ClaimRejectionReason
    detail: str


@dataclass(frozen=True)
class ClaimValidationResult:
    violations: tuple[ClaimViolation, ...] = field(default_factory=tuple)

    @property
    def is_valid(self) -> bool:
        return len(self.violations) == 0


def _rank(order: tuple, value) -> int | None:
    return order.index(value) if value in order else None


def validate_technology_claims(
    *,
    original_text: str,
    proposed_text: str,
    scanner: TechnologyMentionScanner,
    known_skill_names: frozenset[str],
) -> tuple[ClaimViolation, ...]:
    """Section 72, case 1: a job asking for Kubernetes with only Docker
    on the CV must never see a generated bullet claim Kubernetes. A skill
    mentioned in the proposed text that was not already in the original
    text AND is not part of the candidate's genuinely known skill set is
    rejected outright - no amount of "related" evidence justifies
    inventing the exact term.
    """
    original_skills = {skill.canonical_name for skill in scanner.scan(original_text)}
    proposed_skills = {skill.canonical_name for skill in scanner.scan(proposed_text)}
    newly_introduced = proposed_skills - original_skills
    unsupported = newly_introduced - known_skill_names
    if not unsupported:
        return ()
    unsupported_list = ", ".join(sorted(unsupported))
    return (
        ClaimViolation(
            reason=ClaimRejectionReason.UNSUPPORTED_TECHNOLOGY,
            detail=f"Introduces technology not evidenced for this candidate: {unsupported_list}.",
        ),
    )


def validate_certification_claims(*, original_text: str, proposed_text: str) -> tuple[ClaimViolation, ...]:
    """Section 72, case 2: "AWS" on the CV must never become "AWS
    Certified Solutions Architect" in generated text. Certification
    wording ("certified"/"certification"/"certificate") appearing in the
    proposal but absent from the original is rejected - a certification
    can never be inferred from a related skill (Phase 4's own
    anti-inference rule, extended here to generation).
    """
    if _CERTIFICATION_PATTERN.search(proposed_text) and not _CERTIFICATION_PATTERN.search(original_text):
        return (
            ClaimViolation(
                reason=ClaimRejectionReason.UNSUPPORTED_CERTIFICATION,
                detail="Introduces a certification claim not present in the original text.",
            ),
        )
    return ()


def validate_duration_claims(
    *, original_text: str, proposed_text: str, verified_years: float | None
) -> tuple[ClaimViolation, ...]:
    """Section 72, case 3: a candidate with ~2 verified years must never
    see a generated bullet claim "5 years". If a duration figure appears
    in the proposal that was not already in the original AND exceeds the
    independently verified duration (when one is known), it is rejected.
    """
    proposed_years = [float(m.group(1)) for m in _YEARS_PATTERN.finditer(proposed_text)]
    if not proposed_years:
        return ()
    original_years = {float(m.group(1)) for m in _YEARS_PATTERN.finditer(original_text)}
    new_claims = [y for y in proposed_years if y not in original_years]
    if not new_claims:
        return ()
    if verified_years is None:
        # A brand new duration figure with nothing to verify it against -
        # conservative rejection rather than trusting an unverifiable number.
        return (
            ClaimViolation(
                reason=ClaimRejectionReason.DURATION_INFLATION,
                detail="Introduces a duration claim with no verified experience length to check it against.",
            ),
        )
    inflated = [y for y in new_claims if y > verified_years + _DURATION_TOLERANCE_YEARS]
    if not inflated:
        return ()
    return (
        ClaimViolation(
            reason=ClaimRejectionReason.DURATION_INFLATION,
            detail=(
                f"Claims {max(inflated):g} years, exceeding the verified "
                f"{verified_years:g} years of relevant experience."
            ),
        ),
    )


def validate_education_claims(
    *, proposed_text: str, highest_verified_level: EducationLevel
) -> tuple[ClaimViolation, ...]:
    """Section 72, case 5: a Bachelor's-holding candidate must never see
    generated text claim a Master's degree.
    """
    proposed_level = normalize_education_level(proposed_text)
    if proposed_level == EducationLevel.UNKNOWN:
        return ()
    proposed_rank = _rank(_EDUCATION_ORDER, proposed_level)
    verified_rank = _rank(_EDUCATION_ORDER, highest_verified_level)
    if proposed_rank is None:
        return ()
    if verified_rank is None or proposed_rank > verified_rank:
        return (
            ClaimViolation(
                reason=ClaimRejectionReason.EDUCATION_UPGRADE,
                detail=(
                    f"Claims {proposed_level.value}, which is not supported by the "
                    "candidate's verified education."
                ),
            ),
        )
    return ()


def validate_language_claims(
    *, proposed_text: str, verified_proficiency: LanguageProficiency
) -> tuple[ClaimViolation, ...]:
    """Section 72, case 4: "English B2" (INTERMEDIATE/UPPER_INTERMEDIATE)
    must never be rewritten as "native English".
    """
    proposed_level = _detect_proficiency_claim(proposed_text)
    if proposed_level == LanguageProficiency.UNKNOWN:
        return ()
    proposed_rank = _rank(_PROFICIENCY_ORDER, proposed_level)
    verified_rank = _rank(_PROFICIENCY_ORDER, verified_proficiency)
    if proposed_rank is None:
        return ()
    if verified_rank is None or proposed_rank > verified_rank:
        return (
            ClaimViolation(
                reason=ClaimRejectionReason.LANGUAGE_PROFICIENCY_UPGRADE,
                detail=(
                    f"Claims {proposed_level.value} proficiency, which is not supported by the "
                    "candidate's verified level."
                ),
            ),
        )
    return ()


def validate_generated_text(
    *,
    original_text: str,
    proposed_text: str,
    scanner: TechnologyMentionScanner,
    known_skill_names: frozenset[str],
    verified_years: float | None = None,
    highest_education_level: EducationLevel | None = None,
    verified_language_proficiency: LanguageProficiency | None = None,
) -> ClaimValidationResult:
    """The single entry point the Tailoring Engine calls for every
    proposed section (section 18/30). Each check is independently
    testable (see tests/unit/domain/truth/test_claim_validation.py's
    adversarial cases, mirroring section 72 verbatim) and composes here
    without any one check depending on another running first.
    """
    violations: list[ClaimViolation] = []
    violations.extend(
        validate_technology_claims(
            original_text=original_text,
            proposed_text=proposed_text,
            scanner=scanner,
            known_skill_names=known_skill_names,
        )
    )
    violations.extend(validate_certification_claims(original_text=original_text, proposed_text=proposed_text))
    violations.extend(
        validate_duration_claims(
            original_text=original_text, proposed_text=proposed_text, verified_years=verified_years
        )
    )
    if highest_education_level is not None:
        violations.extend(
            validate_education_claims(
                proposed_text=proposed_text, highest_verified_level=highest_education_level
            )
        )
    if verified_language_proficiency is not None:
        violations.extend(
            validate_language_claims(
                proposed_text=proposed_text, verified_proficiency=verified_language_proficiency
            )
        )
    return ClaimValidationResult(violations=tuple(violations))
