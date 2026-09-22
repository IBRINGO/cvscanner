"""Language name and proficiency normalization (Phase 3 section 17).

A small, deliberately curated table of common language names/aliases
(including a few French surface forms, since this codebase's fixtures and
prior sessions have used French-language input) rather than an attempt at
an exhaustive world-language list - quality over quantity, same principle
as the skill taxonomy. An unrecognized language name is preserved as-is
(title-cased) rather than dropped or forced to a guess.
"""
from enum import StrEnum


class LanguageProficiency(StrEnum):
    BEGINNER = "BEGINNER"
    ELEMENTARY = "ELEMENTARY"
    INTERMEDIATE = "INTERMEDIATE"
    UPPER_INTERMEDIATE = "UPPER_INTERMEDIATE"
    ADVANCED = "ADVANCED"
    FLUENT = "FLUENT"
    NATIVE = "NATIVE"
    UNKNOWN = "UNKNOWN"


_CANONICAL_LANGUAGES: dict[str, str] = {}


def _register(canonical: str, *aliases: str) -> None:
    _CANONICAL_LANGUAGES[canonical.lower()] = canonical
    for alias in aliases:
        _CANONICAL_LANGUAGES[alias.lower()] = canonical


_register("English", "anglais")
_register("French", "francais", "français")
_register("Spanish", "espagnol", "espanol")
_register("German", "allemand", "deutsch")
_register("Italian", "italien")
_register("Portuguese", "portugais")
_register("Arabic", "arabe")
_register("Mandarin Chinese", "mandarin", "chinese", "chinois")
_register("Japanese", "japonais")
_register("Russian", "russe")
_register("Dutch", "neerlandais", "néerlandais")
_register("Hindi")
_register("Wolof")
_register("Bambara")

_PROFICIENCY_ALIASES: dict[str, LanguageProficiency] = {
    "beginner": LanguageProficiency.BEGINNER,
    "a1": LanguageProficiency.BEGINNER,
    "elementary": LanguageProficiency.ELEMENTARY,
    "a2": LanguageProficiency.ELEMENTARY,
    "basic": LanguageProficiency.ELEMENTARY,
    "intermediate": LanguageProficiency.INTERMEDIATE,
    "b1": LanguageProficiency.INTERMEDIATE,
    "upper intermediate": LanguageProficiency.UPPER_INTERMEDIATE,
    "b2": LanguageProficiency.UPPER_INTERMEDIATE,
    "advanced": LanguageProficiency.ADVANCED,
    "c1": LanguageProficiency.ADVANCED,
    "professional": LanguageProficiency.ADVANCED,
    "fluent": LanguageProficiency.FLUENT,
    "c2": LanguageProficiency.FLUENT,
    "full professional": LanguageProficiency.FLUENT,
    "native": LanguageProficiency.NATIVE,
    "native speaker": LanguageProficiency.NATIVE,
    "mother tongue": LanguageProficiency.NATIVE,
    "bilingual": LanguageProficiency.NATIVE,
}


def normalize_language_name(raw_name: str) -> str:
    """Returns the canonical English name for a known language, or
    `raw_name` title-cased unchanged if it is not in the curated table -
    the raw value is never discarded.
    """
    key = raw_name.strip().lower()
    return _CANONICAL_LANGUAGES.get(key, raw_name.strip().title())


def normalize_proficiency(raw_proficiency: str | None) -> LanguageProficiency:
    """Never invents a proficiency: missing or unrecognized text
    normalizes to UNKNOWN rather than a guessed default (section 17).
    """
    if not raw_proficiency:
        return LanguageProficiency.UNKNOWN
    return _PROFICIENCY_ALIASES.get(raw_proficiency.strip().lower(), LanguageProficiency.UNKNOWN)
