"""Rule-based, bilingual (EN/FR) section detection.

Started as a deterministic v1 (English-only, string-only heuristics). The
document-intelligence overhaul kept the same shape - SectionType is just
an enum, detect_sections just returns a list, so a smarter classifier can
still replace this later without changing any caller - but replaced two
things that were too weak for real-world CVs:

    1. The heading vocabulary was English-only. It is now bilingual
       (EN/FR), and `_clean()` strips accents before matching, so
       "EXPÉRIENCE", "Expérience professionnelle" and "PROFESSIONAL
       EXPERIENCE" all resolve to the same alias-lookup key. This means a
       single merged lookup table works for both languages without ever
       branching on which language was detected - simpler and more
       robust than maintaining two parallel match paths that could drift
       apart. The detected language is still threaded through and
       attached to each DetectedSection (for evidence/provenance),
       matching the overhaul's required pipeline stage ordering
       (language detection before section detection), even though the
       matching itself doesn't need to branch on it.

    2. Heading detection was a boolean cascade with no way to use
       anything but the line's own text (uppercase-ness, an exact/
       substring alias hit). It is now a weighted score
       (`_heading_score`) that also uses font size, bold, and DOCX
       "Heading style" signals when a layout-aware parser provides them
       (see domain/documents/entities.py's LineRecord) - falling back to
       the original string-only signals when it doesn't (hand-built
       ParsedDocument objects in tests, or a parser that hasn't been
       upgraded), so nothing that worked before regresses.

Shared by CV and job-offer parsing (see domain/job/ use cases) since both
document types have headings that need the same normalization step.
"""
import re
import unicodedata
from statistics import median

from domain.documents.entities import DetectedSection, LineRecord, ParsedDocument
from domain.documents.enums import DocumentLanguage, SectionType
from domain.documents.language import detect_language

# Lowercase, accent-and-punctuation-stripped alias -> canonical SectionType.
# Order does not matter; lookup is by exact normalized match first, then a
# substring pass (see normalize_section_heading). Kept as two separate
# per-language tables (merged into one lookup below) so each language's
# vocabulary can be extended independently and the source of a given
# alias stays obvious - not because matching itself branches on language.
_SECTION_ALIASES_EN: dict[SectionType, frozenset[str]] = {
    SectionType.PERSONAL_INFORMATION: frozenset(
        {
            # --- Formes Standards ---
            "personal info",
            "personal information",
            "contact information",
            "contact info",
            "contact details",
            "contact",
            "contacts",
            "contact personal info",
            
            # --- Variantes d'État Civil & Coordonnées ---
            "personal details",
            "personal profile",  # Parfois pour le résumé, souvent pour l'état civil (UK)
            "identity",
            "address and contact",
            "contact address",
        }
    ),
    SectionType.SUMMARY: frozenset(
        {
            # --- Formes Standards (Résumé de Carrière) ---
            "summary",
            "professional summary",
            "professional profile",
            "executive profile",
            "profile",
            "professional overview",
            "career overview",
            "career focus",
            "executive summary",
            "qualification summary",
            "background summary",
            "personal summary",
            "brief summary",
            
            # --- Formes Orientées "Objectifs" (Candidats Juniors / Reconversion) ---
            "objective",
            "career objective",
            "objective statement",
            "professional objective",
            "job objective",
            "employment objective",
            "personal objective",
            
            # --- Formes Modernes & Digitales ---
            "about",
            "about me",
            "synopsis",
            "introduction",
            "headline",
            "biography",
            "bio",
            "short bio",
        }
    ),

    SectionType.HIGHLIGHTS: frozenset({"highlights", "career highlights", "key highlights"}),
    SectionType.CORE_QUALIFICATIONS: frozenset(
        {"core qualifications", "qualifications summary", "summary of qualifications"}
    ),
    SectionType.EXPERIENCE: frozenset(
        {
            # --- Standards Absolus (Classiques) ---
            "experience",
            "experiences",
            "work experience",
            "work experiences",
            "professional experience",
            "professional experiences",
            "employment history",
            "employment",
            "work history",
            "career history",
            "career summary",  # Parfois confondu avec le profil, mais souvent l'historique complet
            "professional background",
            "background",  # Utilisé comme en-tête générique par certains candidats

            # --- Variantes Spécifiques / Ciblées ---
            "relevant experience",
            "relevant work experience",
            "related experience",
            "applicable experience",
            "key experience",
            "selected experience",
            "selected professional experience",
            "industry experience",
            "corporate experience",

            # --- Formes Techniques & Projets ---
            "technical experience",
            "engineering experience",
            "project experience",
            "freelance experience",
            "freelance",
            "contract work",
            "consulting experience",

            # --- Juniors & Académiques ---
            "internship",
            "internships",
            "internship experience",
            "placement history",
            "placement",
            "placements",
            "academic experience",
            "research experience",
            "teaching experience",
            "co-op experience",  # Très courant aux USA/Canada (Cooperative Education)
            "graduate experience",

            # --- Militaires, Associatifs & Volontariat ---
            "military experience",
            "military history",

            # --- Variantes Courtes & Historiques ---
            "history",
            "record",
            "employment record",
            "professional record",
            "work record",
        }
    ),

    SectionType.EDUCATION: frozenset(
        {
            # --- Formes Standards ---
            "education",
            "educational",
            "education background",
            "educational background",
            "education history",
            "educational history",
            "educational qualifications",
            "education qualifications",
            "education and qualifications",
            "academic background",
            "academic history",
            "academic record",
            "academic credentials",
            "academic qualifications",
            "academics",
            "formal education",
            
            # --- Formations, Cours & Certifications connexes ---
            "training",
            "education training",
            "education and training",
            "training education",
            "training courses",
            "professional training",
            "vocational training",
            "continuing education",
            "further education",
            "coursework",
            "relevant coursework",
            "courses",
            
            # --- Diplômes & Universités ---
            "degrees",
            "degrees and certificates",
            "degrees and certifications",
            "diplomas",
            "studies",
            "university education",
            "college education",
        }
    ),

    SectionType.PROJECTS: frozenset(
        {
            # --- Formes Standards & Clés ---
            "projects",
            "key projects",
            "major projects",
            "selected projects",
            "notable projects",
            "featured projects",
            "professional projects",
            "technical projects",
            "engineering projects",
            
            # --- Personnels & Académiques ---
            "personal projects",
            "side projects",
            "independent projects",
            "academic projects",
            "school projects",
            "university projects",
            "college projects",
            "research projects",
            "capstone projects",  # Très courant dans les universités américaines/canadiennes
            "thesis",
            
            # --- Portfolios & Open Source ---
            "portfolio",
            "project portfolio",
            "open source",
            "open source contributions",
            "development projects",
        }
    ),

    SectionType.SKILLS: frozenset(
        {
            # --- Formes Standards ---
            "skills",
            "key skills",
            "core skills",
            "professional skills",
            "essential skills",
            "relevant skills",
            "selected skills",
            "summary of skills",
            "skills summary",
            
            # --- Compétences & Expertise ---
            "competencies",
            "core competencies",
            "key competencies",
            "professional competencies",
            "skills and competencies",
            "skills & competencies",
            "expertise",
            "skills expertise",
            "areas of expertise",
            "core expertise",
            "area of expertise",
            "professional expertise",
            "proficiencies",
            "technical proficiencies",
            "technical proficiency",
            "capabilities",
            "core capabilities",
            
            # --- Spécificités Techniques & Langues ---
            "it skills",
            "computer skills",
            "software skills",
            "digital skills",
            "hard skills",
            "soft skills",  # Parfois isolé par les candidats
            "languages and skills",
            "technology stack",
            "tools",
            "tools and technologies",
        }
    ),

    SectionType.TECHNICAL_SKILLS: frozenset({"technical skills", "technical expertise"}),
    SectionType.CERTIFICATIONS: frozenset(
        {
            # --- Formes Standards & Synonymes ---
            "certifications",
            "certification",
            "certificates",
            "certificate",
            "licenses",
            "licences",  # Orthographe UK
            "licensure",
            "credentials",
            "professional credentials",
            "professional certifications",
            "professional certificates",
            "professional licenses",
            
            # --- Structures Composées ---
            "licenses and certifications",
            "licenses & certifications",
            "licences and certifications",
            "certifications and licenses",
            "certifications and credentials",
            "accreditations",
            "professional accreditations",
        }
    ),
    SectionType.LANGUAGES: frozenset(
        {
            # --- Formes Standards ---
            "languages",
            "language",
            "language skills",
            "language proficiencies",
            "language proficiency",
            "linguistic skills",
            "linguistic capabilities",
            "spoken languages",
            "foreign languages",
        }
    ),
    SectionType.ACHIEVEMENTS: frozenset(
        {
            # --- Formes Standards & Distinctions ---
            "achievements",
            "professional achievements",
            "key achievements",
            "career achievements",
            "awards",
            "key awards",
            "honors",
            "honours",  # Orthographe UK
            "awards and honors",
            "awards and honours",
            "honors and awards",
            "honours and awards",
            "distinctions",
            "accomplishments",
            "key accomplishments",
            "recognition",
            "professional recognition",
        }
    ),
    SectionType.PUBLICATIONS: frozenset(
        {
            # --- Formes Standards & Dérivés ---
            "publications",
            "published work",
            "published works",
            "selected publications",
            "articles",
            "papers",
            "academic publications",
            "research publications",
            "books and articles",
        }
    ),
    SectionType.PRESENTATIONS: frozenset(
        {
            # --- Formes Standards & Conférences ---
            "presentations",
            "selected presentations",
            "keynote presentations",
            "speaking engagements",
            "speaking",
            "conferences",
            "conference presentations",
            "talks",
            "public speaking",
            "workshops",
        }
    ),
    SectionType.VOLUNTEER_EXPERIENCE: frozenset(
        {
            # --- Formes Standards & Travail Communautaire ---
            "volunteer experience",
            "volunteer experiences",
            "volunteering",
            "volunteer work",
            "volunteer history",
            "community service",
            "community involvement",
            "community experience",
            "social work",
            "pro bono work",
            "pro bono",
            "philanthropy",
        }
    ),
    SectionType.LEADERSHIP: frozenset(
        {
            # --- Formes Standards ---
            "leadership",
            "leadership experience",
            "leadership activities",
            "leadership roles",
            "management experience",
            "extracurricular leadership",
        }
    ),
    SectionType.INTERESTS: frozenset(
        {
            # --- Formes Standards ---
            "interests",
            "personal interests",
            "areas of interest",
            "leisure activities",
            "activities",
        }
    ),
    SectionType.HOBBIES: frozenset(
        {
            # --- Formes Standards & Combinaisons ---
            "hobbies",
            "hobbies and interests",
            "hobbies & interests",
            "interests and hobbies",
            "personal hobbies",
            "pastimes",
        }
    ),
    SectionType.AFFILIATIONS: frozenset(
        {
            # --- Formes Standards & Organismes ---
            "affiliations",
            "professional affiliations",
            "memberships",
            "professional memberships",
            "professional bodies",
            "associations",
            "professional associations",
            "societies",
            "professional societies",
        }
    ),
    SectionType.SCHOLARSHIPS: frozenset(
        {
            # --- Bourses & Financements d'Études ---
            "scholarships",
            "scholarships and awards",
            "scholarships & awards",
            "grants",
            "grants and scholarships",
            "fellowships",
            "academic scholarships",
            "bursaries",  # Très courant au UK / Canada
        }
    ),
    SectionType.ADDITIONAL_INFORMATION: frozenset(
        {
            # --- Informations Diverses ---
            "additional information",
            "additional info",
            "other information",
            "other info",
            "miscellaneous",
            "misc",
            "further information",
            "further info",
            "additional details",
        }
    ),

    SectionType.RESPONSIBILITIES: frozenset(
        {"responsibilities", "what you'll do", "the role", "role", "key responsibilities"}
    ),
    SectionType.REQUIREMENTS: frozenset(
        {
            "requirements",
            "qualifications",
            "what we're looking for",
            "required skills",
            "must have",
        }
    ),
}

# French aliases, written already accent-stripped (matching what _clean()
# produces) - e.g. "expérience" is written "experience" below, which is
# also the English word, so it needs no separate entry; only genuinely
# distinct French vocabulary needs its own alias.
_SECTION_ALIASES_FR: dict[SectionType, frozenset[str]] = {
    SectionType.PERSONAL_INFORMATION: frozenset(
        {
            # --- Formes Standards ---
            "informations personnelles",
            "information personnelle",
            "informations de contact",
            "information de contact",
            "coordonnees",
            "coordonnées",
            "contact",
            "contacts",
            "me contacter",
            
            # --- Variantes Civil et Détails ---
            "etat civil",
            "état civil",
            "informations generales",
            "informations générales",
            "renseignements personnels",  # Très courant au Québec
            "details personnels",
            "détails personnels",
            "a propos de moi",
            "à propos de moi",
        }
    ),
    SectionType.SUMMARY: frozenset(
        {
            # --- Formes Standards (Profil) ---
            "profil",
            "profil professionnel",
            "resume",
            "résumé",
            "resume professionnel",
            "résumé professionnel",
            "presentation",
            "présentation",
            "introduction",
            "vue d'ensemble",
            "synthese",
            "synthèse",
            "synthese professionnelle",
            "synthèse professionnelle",
            "sommaire des qualifications",  # Norme indispensable pour le Canada
            "sommaire professionnel",
            "a propos",
            "à propos",
            
            # --- Formes Orientées "Objectifs" ---
            "objectif",
            "objectifs",
            "objectif professionnel",
            "objectifs professionnels",
            "projet professionnel",
            "aspiration",
            "aspirations",
            
            # --- Formes Courtes / Modernes ---
            "qui suis-je",
            "qui suis je",
            "ma biographie",
            "bio",
            "accroche",
        }
    ),
    SectionType.EXPERIENCE: frozenset(
        {
            # --- Formes Standards ---
            "experience",
            "expérience",
            "experiences",
            "expériences",
            "experience professionnelle",
            "expérience professionnelle",
            "experiences professionnelles",
            "expériences professionnelles",
            "experience de travail",
            "expérience de travail",
            "experiences de travail",
            "expériences de travail",
            
            # --- Variantes Historique & Parcours ---
            "parcours professionnel",
            "parcours professionnels",
            "historique professionnel",
            "antecedents professionnels",
            "antécédents professionnels",
            "carriere",
            "carrière",
            "historique d'emploi",
            "historique d'emplois",
            "experience d'emploi",
            "expérience d'emploi",
            "background professionnel",
            
            # --- Formes Mixtes & Stages ---
            "experience professionnelle et stages",
            "expérience professionnelle et stages",
            "experiences professionnelles et stages",
            "expériences professionnelles et stages",
            "stage",
            "stages",
            "experience de stage",
            "expérience de stage",
            "experiences de stage",
            "expériences de stage",
        }
    ),
    SectionType.EDUCATION: frozenset(
        {
            # --- Formes Standards ---
            "formation",
            "formations",
            "formation academique",
            "formation académique",
            "formations academiques",
            "formations académiques",
            "parcours academique",
            "parcours académique",
            "parcours scolaire",
            "etudes",
            "études",
            "etudes superieures",
            "études supérieures",
            "scolarite",
            "scolarité",  # Majeur pour les CV canadiens
            
            # --- Diplômes & Cursus ---
            "diplome",
            "diplôme",
            "diplomes",
            "diplômes",
            "diplomes et formations",
            "diplômes et formations",
            "titres et diplomes",
            "titres et diplômes",
            "cursus",
            "cursus academique",
            "cursus académique",
            "education",
            "éducation",
            "background academique",
            "background académique",
            "enseignements",
        }
    ),
    SectionType.PROJECTS: frozenset(
        {
            "projet",
            "projets",
            "projets personnels",
            "projet personnel",
            "projets academiques",
            "projets académiques",
            "projet academique",
            "projet académique",
            "projets notables",
            "projets cles",
            "projets clés",
            "realisations techniques",
            "réalisations techniques",
            "projets professionnels",
            "portfolio",
            "travaux",
        }
    ),
    SectionType.SKILLS: frozenset(
        {
            "competence",
            "compétence",
            "competences",
            "compétences",
            "competences professionnelles",
            "compétences professionnelles",
            "competences cles",
            "compétences clés",
            "competences de base",
            "compétences de base",
            "domaines de competence",
            "domaines de compétence",
            "domaines de competences",
            "domaines de compétences",
            "resume des competences",
            "résumé des compétences",
            "savoir-faire",
            "savoir faire",
            "aptitudes",
            "atouts",
        }
    ),
    SectionType.TECHNICAL_SKILLS: frozenset(
        {
            "competences techniques",
            "compétences techniques",
            "competence technique",
            "compétence technique",
            "expertise technique",
            "expertises techniques",
            "competences informatiques",
            "compétences informatiques",
            "competences logicielles",
            "compétences logicielles",
            "competences digitales",
            "compétences digitales",
            "maitrise technique",
            "maîtrise technique",
            "technologies",
            "outils",
            "outils et technologies",
            "environnement technique",
            "environnements techniques",
            "competences it",
            "compétences it",
        }
    ),
    SectionType.CERTIFICATIONS: frozenset(
        {
            "certificat",
            "certificats",
            "certification",
            "certifications",
            "accreditation",
            "accréditation",
            "accreditations",
            "accréditations",
            "licence",
            "licences",
            "permis",
            "certifications professionnelles",
            "certificats professionnels",
            "habilitations",
            "attestations",
        }
    ),
    SectionType.LANGUAGES: frozenset(
        {
            "langue",
            "langues",
            "langues vivantes",
            "competences linguistiques",
            "compétences linguistiques",
            "langues maitrisees",
            "langues maîtrisées",
            "connaissances linguistiques",
        }
    ),
    SectionType.ACHIEVEMENTS: frozenset(
        {
            "realisation",
            "réalisation",
            "realisations",
            "réalisations",
            "distinction",
            "distinctions",
            "prix",
            "recompense",
            "récompense",
            "recompenses",
            "récompenses",
            "honneurs",
            "succes",
            "succès",
            "accomplissements",
            "palmares",
            "palmarès",
        }
    ),
    SectionType.VOLUNTEER_EXPERIENCE: frozenset(
        {
            "benevolat",
            "bénévolat",
            "benevole",
            "bénévole",
            "experience de benevolat",
            "expérience de bénévolat",
            "experiences de benevolat",
            "expériences de bénévolat",
            "experience associative",
            "expérience associative",
            "experiences associatives",
            "expériences associatives",
            "volontariat",
            "engagement associatif",
            "engagement citoyen",
            "activites associatives",
            "activités associatives",
            "travail communautaire",  # Courant au Québec/Belgique
        }
    ),
    SectionType.INTERESTS: frozenset(
        {
            "centres d'interet",
            "centres d'intérêt",
            "centre d'interet",
            "centre d'intérêt",
            "interets",
            "intérêts",
            "centres d'interets",
            "centres d'intérêts",
            "activites extra-professionnelles",
            "activités extra-professionnelles",
            "activites annexes",
            "activités annexes",
        }
    ),
    SectionType.HOBBIES: frozenset(
        {
            "loisir",
            "loisirs",
            "passions",
            "passion",
            "hobbies",
            "hobby",
            "loisirs et interets",
            "loisirs et intérêts",
        }
    ),
    SectionType.AFFILIATIONS: frozenset(
        {
            "association",
            "associations",
            "affiliation",
            "affiliations",
            "affiliations professionnelles",
            "membre",
            "organisations",
            "societes professionnelles",
            "sociétés professionnelles",
            "adhesions",
            "adhésions",
        }
    ),
    SectionType.ADDITIONAL_INFORMATION: frozenset(
        {
            "informations complementaires",
            "informations complémentaires",
            "information complementaire",
            "information complémentaire",
            "informations additionnelles",
            "information additionnelle",
            "divers",
            "autres informations",
            "autre information",
            "renseignements complementaires",
            "renseignements complémentaires",
            "details complementaires",
            "détails complémentaires",
            "plus d'informations",
            "plus d'infos",
        }
    ),
}

# Merged, bilingual view - kept under the original name so any existing
# caller/test importing SECTION_ALIASES directly still sees a superset of
# what it used to (additive only, no alias removed except the
# intentional "qualifications"/EDUCATION fix below).
SECTION_ALIASES: dict[SectionType, frozenset[str]] = {
    section_type: _SECTION_ALIASES_EN.get(section_type, frozenset())
    | _SECTION_ALIASES_FR.get(section_type, frozenset())
    for section_type in set(_SECTION_ALIASES_EN) | set(_SECTION_ALIASES_FR)
}

_MAX_HEADING_LENGTH = 45
_HEADING_LOOKUP: dict[str, SectionType] = {
    alias: section_type for section_type, aliases in SECTION_ALIASES.items() for alias in aliases
}

# A line whose combined signal score reaches this is treated as a
# heading. Calibrated so a bare alias hit (0.6) or an all-caps short line
# (0.35) plus any one secondary signal (font size, bold, substring match)
# crosses it, while a single weak signal alone never does.
_HEADING_SCORE_THRESHOLD = 0.5
_HEADING_FONT_SIZE_RATIO = 1.15


def normalize_section_heading(raw_heading: str) -> SectionType:
    """Maps a raw heading string (e.g. "Professional Experience", or
    "Expérience professionnelle") to a canonical SectionType. Falls back
    to OTHER rather than guessing.
    """
    cleaned = _clean(raw_heading)
    if cleaned in _HEADING_LOOKUP:
        return _HEADING_LOOKUP[cleaned]

    # Substring pass: "professional experience section" still matches
    # "experience". Longer aliases are checked first so "work experience"
    # wins over a shorter coincidental match.
    for alias in sorted(_HEADING_LOOKUP, key=len, reverse=True):
        if alias in cleaned:
            return _HEADING_LOOKUP[alias]

    return SectionType.OTHER


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _clean(text: str) -> str:
    stripped = re.sub(r"[^a-z0-9' ]", " ", _strip_accents(text.strip().lower()))
    return " ".join(stripped.split())


def _heading_score(
    text: str,
    *,
    font_size: float | None = None,
    is_bold: bool | None = None,
    is_heading_style: bool = False,
    typical_font_size: float | None = None,
) -> float:
    """Combines multiple weak signals into one heading-likelihood score
    instead of the single boolean cascade this used to be - see the
    module docstring. Each signal is named so the result stays
    explainable (section 12 of the overhaul brief: "deterministic and
    explainable"), and no single weak signal alone can cross the
    threshold.
    """
    stripped = text.strip()
    if not stripped or len(stripped) > _MAX_HEADING_LENGTH:
        return 0.0
    if stripped.endswith((".", ",", ";")):
        return 0.0

    score = 0.0

    # A word-processor's own "Heading" paragraph style is near-certain -
    # the author explicitly marked this as a heading (see docx_parser.py).
    if is_heading_style:
        score += 0.9

    cleaned = _clean(stripped)
    if cleaned in _HEADING_LOOKUP:
        score += 0.6

    # `len(stripped) >= 5` keeps short all-caps acronyms that are really
    # just skill tokens (AWS, SQL, GCP, CSS) from being misread as a new
    # section heading - every real heading this module recognizes is at
    # least 5 characters long ("SKILLS" is the shortest).
    if stripped.isupper() and len(stripped.split()) <= 6 and len(stripped) >= 5:
        score += 0.35

    if font_size and typical_font_size and font_size >= typical_font_size * _HEADING_FONT_SIZE_RATIO:
        score += 0.3

    if is_bold:
        score += 0.15

    # The substring fallback only counts for short, heading-shaped lines.
    # Without this gate, a sentence that merely mentions a keyword (e.g.
    # "5+ years of experience", "familiar with core competencies") would
    # score just because "experience"/"competencies" appears in it.
    if len(cleaned.split()) <= 3 and normalize_section_heading(stripped) != SectionType.OTHER:
        score += 0.25

    return min(score, 1.0)


def detect_sections(
    parsed: ParsedDocument, language: DocumentLanguage | None = None
) -> list[DetectedSection]:
    """Splits a parsed document into sections at heading-like lines.

    `language` is normally left as None - the document's language is
    then detected once from `parsed.raw_text` (see domain/documents/
    language.py) and attached to every returned DetectedSection. Callers
    that already ran language detection upstream (see application/cv/
    process_pipeline.py) pass it explicitly so it isn't computed twice.

    Text before the first detected heading is not discarded - it is
    returned as a leading SectionType.OTHER section (typically the name/
    contact block at the top of a CV, or the job title block at the top
    of a job offer).
    """
    doc_language = language if language is not None else detect_language(parsed.raw_text).language

    lines = _lines_from_document(parsed)
    if not lines:
        return []

    typical_font_size = _typical_font_size(lines)

    sections: list[DetectedSection] = []
    current_type = SectionType.OTHER
    current_heading = ""
    current_page: int | None = lines[0].page_number
    current_column: int | None = lines[0].column_index
    current_confidence = 1.0
    current_lines: list[str] = []

    def flush() -> None:
        body = "\n".join(current_lines).strip()
        if body or current_heading:
            sections.append(
                DetectedSection(
                    section_type=current_type,
                    heading_text=current_heading,
                    body_text=body,
                    page_number=current_page,
                    language=doc_language,
                    confidence=current_confidence,
                    column_index=current_column,
                )
            )

    for line in lines:
        score = _heading_score(
            line.text,
            font_size=line.font_size,
            is_bold=line.is_bold,
            is_heading_style=line.is_heading_style,
            typical_font_size=typical_font_size,
        )
        if score >= _HEADING_SCORE_THRESHOLD:
            flush()
            current_type = normalize_section_heading(line.text)
            current_heading = line.text.strip()
            current_page = line.page_number
            current_column = line.column_index
            current_confidence = score
            current_lines = []
        else:
            current_lines.append(line.text)

    flush()
    return sections


def _typical_font_size(lines: list[LineRecord]) -> float | None:
    sizes = [line.font_size for line in lines if line.font_size]
    return median(sizes) if sizes else None


def _lines_from_document(parsed: ParsedDocument) -> list[LineRecord]:
    """The line sequence detect_sections walks, in final reading order.

    Prefers `parsed.line_records` (already column-ordered and font-aware
    - see LineRecord's docstring) when a layout-aware parser provided it;
    falls back to the pre-overhaul flat page-text split otherwise, so
    every hand-built ParsedDocument in existing tests (which never set
    line_records) behaves exactly as before.
    """
    if parsed.line_records:
        return list(parsed.line_records)

    return [LineRecord(page_number=page_number, text=text) for page_number, text in _flatten_lines(parsed)]


def _flatten_lines(parsed: ParsedDocument) -> list[tuple[int | None, str]]:
    """Line-by-line (page_number, line) pairs, preserving page boundaries
    when the parser provided them (PDF); page_number is None throughout
    for formats without page semantics (DOCX) - see
    domain/documents/entities.py's ParsedBlock docstring.

    Blank lines are kept (not filtered): they are the paragraph-boundary
    signal extractors use to split a section's body into separate entries
    (e.g. two Experience entries), via `body_text.split("\\n\\n")`.
    """
    if parsed.pages:
        result: list[tuple[int | None, str]] = []
        for page in parsed.pages:
            for line in page.text.splitlines():
                result.append((page.page_number, line))
        return result

    return [(None, line) for line in parsed.raw_text.splitlines()]
