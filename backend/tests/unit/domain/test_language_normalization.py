from domain.cv.language_normalization import (
    LanguageProficiency,
    normalize_language_name,
    normalize_proficiency,
)


class TestNormalizeLanguageName:
    def test_maps_french_surface_forms_to_canonical_english_name(self):
        assert normalize_language_name("anglais") == "English"
        assert normalize_language_name("Anglais") == "English"
        assert normalize_language_name("français") == "French"

    def test_maps_english_surface_forms_to_canonical_name(self):
        assert normalize_language_name("English") == "English"
        assert normalize_language_name("english language") != "English"  # not a registered alias

    def test_unrecognized_language_is_preserved_title_cased(self):
        assert normalize_language_name("klingon") == "Klingon"


class TestNormalizeProficiency:
    def test_maps_cefr_codes(self):
        assert normalize_proficiency("B2") == LanguageProficiency.UPPER_INTERMEDIATE
        assert normalize_proficiency("c2") == LanguageProficiency.FLUENT

    def test_maps_native_aliases(self):
        assert normalize_proficiency("native speaker") == LanguageProficiency.NATIVE
        assert normalize_proficiency("mother tongue") == LanguageProficiency.NATIVE
        assert normalize_proficiency("bilingual") == LanguageProficiency.NATIVE

    def test_never_invents_a_proficiency_for_missing_or_unknown_text(self):
        assert normalize_proficiency(None) == LanguageProficiency.UNKNOWN
        assert normalize_proficiency("") == LanguageProficiency.UNKNOWN
        assert normalize_proficiency("expert-ish") == LanguageProficiency.UNKNOWN
