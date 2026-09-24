"""Document-language detection: what natural language a CV or job offer
is *written in* - not to be confused with domain/cv/language_normalization.py's
`LanguageProficiency`, which describes a language the *candidate speaks*.

Deliberately dependency-free and deterministic (see the document-
intelligence overhaul's quality bar: "the implementation must be
deterministic and explainable... prefer strong layout analysis + bilingual
linguistic knowledge + deterministic scoring" over reaching for an LLM or
even a statistical language-ID library). A CV is typically 150-600 words
of running text, which is comfortably enough for stopword/marker-frequency
signals to be reliable without any model file or native dependency - the
same reasoning that led this codebase to prefer pdfplumber over a
heavier PDF library (see pdf_parser.py's docstring).

Three independent, named signals are combined into one score per
candidate language:

    1. Stop-word frequency - the most reliable signal for CV-length text.
    2. Diacritic density - French-specific accented characters are a
       strong, cheap tell.
    3. Elision/contraction markers - "l'expérience"/"qu'il" (French) vs
       "it's"/"don't" (English) are near-unambiguous per-language tells.

Extensible by design: adding a language later (Spanish, German, Arabic -
see docs/architecture) means adding one `DocumentLanguage` member
(domain/documents/enums.py) and one `_LanguageSignals` entry below, not
restructuring this module or its callers.
"""
import re
from dataclasses import dataclass

from domain.documents.enums import DocumentLanguage

# Below this confidence, the losing language still had a meaningful
# presence worth surfacing (e.g. a French CV with an English "Skills"
# heading, or a genuinely bilingual document) - see section 2 of the
# overhaul brief: "A CV containing both French and English headings must
# still be handled correctly."
_BILINGUAL_THRESHOLD = 0.75
_MIN_SIGNAL_WORDS = 4

_FR_DIACRITICS = frozenset("éèêëàâäîïôöùûüÿçœæ")

_FR_STOPWORDS = frozenset(
    {
        "le", "la", "les", "un", "une", "des", "du", "de", "et", "à", "au", "aux",
        "en", "dans", "pour", "avec", "sur", "par", "est", "sont", "ce", "cet",
        "cette", "ces", "son", "sa", "ses", "qui", "que", "quoi", "dont", "où",
        "ne", "pas", "plus", "mais", "ou", "donc", "or", "ni", "car", "je", "tu",
        "il", "elle", "nous", "vous", "ils", "elles", "mon", "ton", "notre",
        "votre", "leur", "leurs", "été", "être", "avoir", "fait", "faire",
        "sans", "entre", "depuis", "chez", "vers", "ans", "années", "née", "né",
        "autre", "tout", "tous", "toute", "toutes", "comme", "aussi", "très",
    }
)
_EN_STOPWORDS = frozenset(
    {
        "the", "an", "and", "or", "but", "of", "to", "in", "on", "at", "for",
        "with", "by", "from", "is", "are", "was", "were", "be", "been", "being",
        "this", "that", "these", "those", "it", "its", "he", "she", "they", "we",
        "you", "as", "not", "have", "has", "had", "will", "would", "can", "could",
        "about", "into", "than", "then", "so", "such", "which", "who", "whom",
        "their", "our", "your", "my", "years", "using", "including", "across",
    }
)

_FR_MARKER_RE = re.compile(r"\b[ldjmnstc]['’]|qu['’]", re.IGNORECASE)
_EN_MARKER_RE = re.compile(r"\b\w+['’](s|t|re|ve|ll|d|m)\b", re.IGNORECASE)
_WORD_RE = re.compile(r"[a-zA-ZÀ-ÿ']+")


@dataclass(frozen=True)
class DetectedLanguage:
    """The result of `detect_language()`. `confidence` is in [0.0, 1.0];
    0.0 means "not enough signal to tell" (language is then UNKNOWN,
    never a guess). `secondary_language` is set only when the losing
    language still had a real presence - see `_BILINGUAL_THRESHOLD`.
    """

    language: DocumentLanguage
    confidence: float
    secondary_language: DocumentLanguage | None = None


def detect_language(text: str) -> DetectedLanguage:
    """Deterministically detects whether `text` is written in French or
    English, from multiple weighted signals (see module docstring).
    Never raises; returns UNKNOWN with confidence 0.0 rather than
    guessing when there isn't enough signal (an empty document, or one
    that is almost entirely numbers/symbols).
    """
    if not text or not text.strip():
        return DetectedLanguage(language=DocumentLanguage.UNKNOWN, confidence=0.0)

    words = [w.lower() for w in _WORD_RE.findall(text)]
    if len(words) < _MIN_SIGNAL_WORDS:
        return DetectedLanguage(language=DocumentLanguage.UNKNOWN, confidence=0.0)

    fr_stopword_hits = sum(1 for w in words if w in _FR_STOPWORDS)
    en_stopword_hits = sum(1 for w in words if w in _EN_STOPWORDS)
    diacritic_hits = sum(1 for ch in text if ch.lower() in _FR_DIACRITICS)
    fr_marker_hits = len(_FR_MARKER_RE.findall(text))
    en_marker_hits = len(_EN_MARKER_RE.findall(text))

    fr_score = fr_stopword_hits + diacritic_hits * 1.5 + fr_marker_hits * 2.0
    en_score = en_stopword_hits + en_marker_hits * 2.0
    total = fr_score + en_score

    if total == 0:
        return DetectedLanguage(language=DocumentLanguage.UNKNOWN, confidence=0.0)

    if fr_score >= en_score:
        primary, primary_score, secondary_score = DocumentLanguage.FR, fr_score, en_score
    else:
        primary, primary_score, secondary_score = DocumentLanguage.EN, en_score, fr_score

    confidence = round(primary_score / total, 4)
    secondary_language = None
    if secondary_score > 0 and confidence < _BILINGUAL_THRESHOLD:
        secondary_language = DocumentLanguage.EN if primary == DocumentLanguage.FR else DocumentLanguage.FR

    return DetectedLanguage(language=primary, confidence=confidence, secondary_language=secondary_language)
