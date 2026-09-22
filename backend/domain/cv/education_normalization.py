"""Education level normalization (Phase 3 section 16).

Maps a raw degree string ("BSc", "Licence", "Master's Degree") to a small
controlled vocabulary while always preserving the original text - callers
keep both the raw `degree` field already on domain/cv/entities.py::Education
and this normalized level; neither replaces the other.
"""
import re
from enum import StrEnum


class EducationLevel(StrEnum):
    HIGH_SCHOOL = "HIGH_SCHOOL"
    ASSOCIATE = "ASSOCIATE"
    BACHELOR = "BACHELOR"
    MASTER = "MASTER"
    DOCTORATE = "DOCTORATE"
    PROFESSIONAL_CERTIFICATE = "PROFESSIONAL_CERTIFICATE"
    UNKNOWN = "UNKNOWN"


# Order matters: "Master of Business Administration" must resolve to
# MASTER before a looser pattern gets a chance to misfire, and doctorate
# variants are checked before "master" so "Doctor of..." never matches a
# stray "master" substring.
_EDUCATION_KEYWORDS: tuple[tuple[EducationLevel, re.Pattern[str]], ...] = (
    (
        EducationLevel.DOCTORATE,
        re.compile(r"\b(phd|ph\.d|doctorate|doctoral)\b", re.IGNORECASE),
    ),
    (
        EducationLevel.MASTER,
        re.compile(r"\b(master|msc|m\.sc|mba|ma|meng|m\.eng)\b", re.IGNORECASE),
    ),
    (
        EducationLevel.BACHELOR,
        re.compile(
            r"\b(bachelor|licence|licence professionnelle|bsc|b\.sc|ba|beng|b\.eng)\b",
            re.IGNORECASE,
        ),
    ),
    (
        EducationLevel.ASSOCIATE,
        re.compile(r"\b(associate degree|bts|dut|diplome universitaire)\b", re.IGNORECASE),
    ),
    (
        EducationLevel.PROFESSIONAL_CERTIFICATE,
        re.compile(r"\b(certificate|certification|professional diploma)\b", re.IGNORECASE),
    ),
    (
        EducationLevel.HIGH_SCHOOL,
        re.compile(r"\b(high school|baccalaureat|baccalauréat|diploma)\b", re.IGNORECASE),
    ),
)


def normalize_education_level(raw_degree: str | None) -> EducationLevel:
    """Returns the education level implied by `raw_degree`'s wording.
    Ambiguous or unrecognized wording normalizes to UNKNOWN - never
    guessed from unrelated context (e.g. the institution name).
    """
    if not raw_degree:
        return EducationLevel.UNKNOWN

    for level, pattern in _EDUCATION_KEYWORDS:
        if pattern.search(raw_degree):
            return level

    return EducationLevel.UNKNOWN
