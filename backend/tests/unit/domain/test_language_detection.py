from domain.documents.enums import DocumentLanguage
from domain.documents.language import detect_language

_EN_CV = """Jordan Rivera
Backend engineer with experience building distributed systems for the team.
He has worked with the platform and led several projects across the company.
"""

_FR_CV = """Camille Dubois
Ingenieure back-end avec de l'experience dans la creation de systemes distribues.
Elle a travaille sur la plateforme et dirige plusieurs projets pour l'entreprise.
"""


class TestDetectLanguage:
    def test_detects_english_with_high_confidence(self):
        result = detect_language(_EN_CV)
        assert result.language == DocumentLanguage.EN
        assert result.confidence > 0.8
        assert result.secondary_language is None

    def test_detects_french_with_high_confidence(self):
        result = detect_language(_FR_CV)
        assert result.language == DocumentLanguage.FR
        assert result.confidence > 0.8
        assert result.secondary_language is None

    def test_detects_french_via_diacritics_and_elision_even_without_much_text(self):
        result = detect_language("Ingenieure chez l'entreprise, experience de l'equipe qu'il a menee.")
        assert result.language == DocumentLanguage.FR

    def test_empty_text_is_unknown_not_a_guess(self):
        result = detect_language("")
        assert result.language == DocumentLanguage.UNKNOWN
        assert result.confidence == 0.0

    def test_too_little_text_is_unknown_not_a_guess(self):
        result = detect_language("Jordan Rivera")
        assert result.language == DocumentLanguage.UNKNOWN
        assert result.confidence == 0.0

    def test_a_genuinely_mixed_document_gets_low_confidence_and_a_secondary_language(self):
        mixed = (
            "Experience professionnelle chez Meridian Analytics, de janvier a mars, "
            "avec une equipe de plusieurs personnes dans notre entreprise.\n"
            "Software Engineer at Meridian Analytics, from January to March.\n"
            "Built and maintained the billing service for the company and the team.\n"
        )
        result = detect_language(mixed)
        assert result.confidence < 0.75
        assert result.secondary_language is not None
        assert result.secondary_language != result.language

    def test_a_french_cv_with_a_few_english_section_headings_still_resolves_to_french(self):
        # Section 2 of the overhaul brief: "A CV containing both French
        # and English headings must still be handled correctly." Section
        # headings ("Skills", "Education") are content words, not
        # function words, so they don't dilute the dominant language's
        # stopword signal the way a fully bilingual paragraph would.
        text = _FR_CV + "\n\nSKILLS\nPython, Django\n\nEDUCATION\nMaster en informatique"
        result = detect_language(text)
        assert result.language == DocumentLanguage.FR
