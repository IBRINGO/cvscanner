"""Regenerates the synthetic test fixtures in this directory.

Not part of the test suite itself (pytest's `test_*.py` collection rule
skips it) - run manually when a fixture needs to change:

    python tests/fixtures/generate_fixtures.py

All content is synthetic (a fictional candidate and a fictional job
offer) - see section 55 of the Phase 2 brief ("no real people's private
CVs"). Requires `reportlab` (dev-only dependency, see pyproject.toml).

Document-intelligence overhaul additions: fixtures covering the new
capabilities (bilingual parsing, two-column layout, multi-page, unusual/
missing headings, varied fonts, DOCX tables) - see each builder's
docstring for what it specifically exercises.
"""
from pathlib import Path

from docx import Document
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

FIXTURES_DIR = Path(__file__).parent
PAGE_WIDTH, PAGE_HEIGHT = LETTER

CV_LINES = [
    "Jordan Rivera",
    "jordan.rivera@example.com | +1 415 555 0199",
    "San Francisco, CA",
    "",
    "SUMMARY",
    "Backend engineer with 6 years of experience building distributed systems.",
    "",
    "EXPERIENCE",
    "Senior Backend Engineer, Meridian Analytics",
    "January 2020 - Present",
    "Led the migration of the core billing service to a microservice architecture.",
    "- Reduced API latency by 40 percent",
    "- Mentored a team of four engineers",
    "Technologies: Python, Django, PostgreSQL, Docker",
    "",
    "Software Engineer, Northwind Labs",
    "June 2017 - December 2019",
    "Built internal tooling for the data platform team.",
    "Technologies: Python, Flask, Redis",
    "",
    "EDUCATION",
    "BSc Computer Science, University of Washington",
    "2013 - 2017",
    "",
    "SKILLS",
    "Python, Django, PostgreSQL, Docker, React, Git",
    "",
    "CERTIFICATIONS",
    "AWS Certified Solutions Architect, Amazon, 2021",
    "",
    "LANGUAGES",
    "English - Native",
    "Spanish - Conversational",
]

# A French counterpart to CV_LINES - same shape/content, French headings
# and prose, real accented characters (reportlab's base-14 fonts use a
# WinAnsi-compatible encoding that supports them).
CV_LINES_FR = [
    "Camille Dubois",
    "camille.dubois@example.fr | +33 6 12 34 56 78",
    "Paris, France",
    "",
    "PROFIL",
    "Ingenieure back-end avec 6 annees d'experience dans la conception de systemes distribues.",
    "",
    "EXPERIENCE PROFESSIONNELLE",
    "Ingenieure back-end senior, Meridian Analytics",
    "Janvier 2020 - Present",
    "A dirige la migration du service de facturation vers une architecture de microservices.",
    "- Reduction de la latence de l'API de 40 pour cent",
    "- Encadrement d'une equipe de quatre ingenieurs",
    "Technologies : Python, Django, PostgreSQL, Docker",
    "",
    "Ingenieure logicielle, Northwind Labs",
    "Juin 2017 - Decembre 2019",
    "A construit des outils internes pour l'equipe data.",
    "Technologies : Python, Flask, Redis",
    "",
    "FORMATION",
    "Master en informatique, Universite de Paris",
    "2013 - 2017",
    "",
    "COMPETENCES",
    "Python, Django, PostgreSQL, Docker, React, Git",
    "",
    "CERTIFICATIONS",
    "AWS Certified Solutions Architect, Amazon, 2021",
    "",
    "LANGUES",
    "Francais - Natif",
    "Anglais - Courant",
]

JOB_TEXT = """Senior Backend Engineer
Company: Meridian Analytics
Location: Remote
Employment Type: Full-time
Seniority: Senior

SUMMARY
We are looking for an experienced backend engineer to join our platform team.

RESPONSIBILITIES
- Design and maintain REST APIs
- Collaborate with product and design teams
- Mentor junior engineers

REQUIREMENTS
Required:
Python
Django
PostgreSQL
5+ years of experience
Bachelor degree in Computer Science

Preferred:
Docker
Kubernetes
AWS
"""


def _draw_single_column(pdf: canvas.Canvas, lines: list[str], line_height: int = 16) -> None:
    y = PAGE_HEIGHT - 50
    for line in lines:
        pdf.drawString(50, y, line)
        y -= line_height
        if y < 50:
            pdf.showPage()
            y = PAGE_HEIGHT - 50


def build_cv_pdf() -> None:
    output_path = FIXTURES_DIR / "sample_cv.pdf"
    pdf = canvas.Canvas(str(output_path), pagesize=LETTER)
    _draw_single_column(pdf, CV_LINES)
    pdf.save()


def build_cv_docx() -> None:
    output_path = FIXTURES_DIR / "sample_cv.docx"
    document = Document()
    for line in CV_LINES:
        document.add_paragraph(line)
    document.save(str(output_path))


def build_job_offer_txt() -> None:
    (FIXTURES_DIR / "sample_job_offer.txt").write_text(JOB_TEXT, encoding="utf-8")


def build_job_offer_docx() -> None:
    output_path = FIXTURES_DIR / "sample_job_offer.docx"
    document = Document()
    for line in JOB_TEXT.split("\n"):
        document.add_paragraph(line)
    document.save(str(output_path))


def build_corrupted_pdf() -> None:
    (FIXTURES_DIR / "corrupted.pdf").write_bytes(b"%PDF-1.4\nnot a real pdf body" + bytes(range(256)) * 4)


def build_empty_pdf() -> None:
    (FIXTURES_DIR / "empty.pdf").write_bytes(b"")


def build_unsupported_file() -> None:
    (FIXTURES_DIR / "unsupported.exe").write_bytes(b"MZ\x90\x00" + b"\x00" * 32)


# --- Document-intelligence overhaul fixtures -------------------------------


def build_cv_fr_pdf() -> None:
    """A single-column French CV - same shape as sample_cv.pdf, entirely
    French headings/prose, to prove language detection and the French
    half of the bilingual taxonomy independent of any layout complexity.
    """
    output_path = FIXTURES_DIR / "sample_cv_fr.pdf"
    pdf = canvas.Canvas(str(output_path), pagesize=LETTER)
    _draw_single_column(pdf, CV_LINES_FR)
    pdf.save()


def build_cv_fr_docx() -> None:
    output_path = FIXTURES_DIR / "sample_cv_fr.docx"
    document = Document()
    for line in CV_LINES_FR:
        document.add_paragraph(line)
    document.save(str(output_path))


def _draw_two_column_cv(
    output_path: Path,
    *,
    name: str,
    contact: str,
    left_heading: str,
    left_lines: list[str],
    right_heading: str,
    right_lines: list[str],
) -> None:
    """A single-page, two-column CV: a full-width name/contact header,
    then a left column (`left_heading` + `left_lines`) and a right column
    (`right_heading` + `right_lines`) drawn independently at x=50 and
    x=320 respectively - real column geometry a naive top-to-bottom text
    extraction would interleave, which is exactly the bug this fixture
    exists to catch (see pdf_parser.py's module docstring).
    """
    pdf = canvas.Canvas(str(output_path), pagesize=LETTER)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, PAGE_HEIGHT - 50, name)
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, PAGE_HEIGHT - 68, contact)

    body_top = PAGE_HEIGHT - 100
    line_height = 16

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, body_top, left_heading)
    pdf.drawString(320, body_top, right_heading)

    pdf.setFont("Helvetica", 10)
    y = body_top - 20
    for line in left_lines:
        if line:
            pdf.drawString(50, y, line)
        y -= line_height

    y = body_top - 20
    for line in right_lines:
        if line:
            pdf.drawString(320, y, line)
        y -= line_height

    pdf.save()


def build_cv_two_column_en_pdf() -> None:
    """English two-column CV: SKILLS/CERTIFICATIONS in the left sidebar,
    EXPERIENCE in the main right column - deliberately different section
    types per column (scenario 12 of the overhaul's test list), each
    spanning enough rows to pass column detection's "spread across the
    page" gate.
    """
    _draw_two_column_cv(
        FIXTURES_DIR / "sample_cv_two_column_en.pdf",
        name="Taylor Morgan",
        contact="taylor.morgan@example.com | +1 212 555 0134",
        left_heading="SKILLS",
        left_lines=[
            "Python",
            "Django",
            "PostgreSQL",
            "Docker",
            "Kubernetes",
            "Git",
            "",
            "CERTIFICATIONS",
            "AWS Certified Developer, 2022",
        ],
        right_heading="EXPERIENCE",
        right_lines=[
            "Senior Platform Engineer, Beacon Systems",
            "March 2019 - Present",
            "Led the platform reliability initiative across three teams.",
            "- Cut deployment time by half",
            "",
            "Platform Engineer, Nimbus Cloud",
            "July 2015 - February 2019",
            "Maintained the internal Kubernetes platform.",
        ],
    )


def build_cv_two_column_fr_pdf() -> None:
    """French two-column CV - same layout as the English one, French
    headings/content, so column detection and bilingual taxonomy are
    both exercised together (this is the specific combination the
    overhaul brief calls out as the highest-risk case)."""
    _draw_two_column_cv(
        FIXTURES_DIR / "sample_cv_two_column_fr.pdf",
        name="Sacha Bernard",
        contact="sacha.bernard@example.fr | +33 6 98 76 54 32",
        left_heading="COMPETENCES",
        left_lines=[
            "Python",
            "Django",
            "PostgreSQL",
            "Docker",
            "Kubernetes",
            "Git",
            "",
            "CERTIFICATIONS",
            "AWS Certified Developer, 2022",
        ],
        right_heading="EXPERIENCE PROFESSIONNELLE",
        right_lines=[
            "Ingenieure plateforme senior, Beacon Systems",
            "Mars 2019 - Present",
            "A dirige l'initiative de fiabilite de la plateforme sur trois equipes.",
            "- Reduction du temps de deploiement de moitie",
            "",
            "Ingenieure plateforme, Nimbus Cloud",
            "Juillet 2015 - Fevrier 2019",
            "A maintenu la plateforme Kubernetes interne.",
        ],
    )


def build_cv_bilingual_pdf() -> None:
    """A CV whose body is French but whose section headings are a mix of
    French and English (common in real bilingual-market CVs - e.g.
    Quebec, Switzerland, international teams) - language detection must
    still resolve one dominant document language (French, by word
    volume) while both headings still normalize correctly (section 2 of
    the overhaul brief: "A CV containing both French and English
    headings must still be handled correctly")."""
    lines = [
        "Morgane Lefevre",
        "morgane.lefevre@example.com | +33 6 11 22 33 44",
        "Lyon, France",
        "",
        "PROFIL",
        "Ingenieure back-end avec 6 annees d'experience dans la conception de systemes distribues.",
        "",
        "EXPERIENCE PROFESSIONNELLE",
        "Ingenieure back-end senior, Meridian Analytics",
        "Janvier 2020 - Present",
        "A dirige la migration du service de facturation vers une architecture de microservices.",
        "",
        "SKILLS",
        "Python, Django, PostgreSQL, Docker",
        "",
        "EDUCATION",
        "Master en informatique, Universite de Paris",
        "2013 - 2017",
        "",
        "LANGUES",
        "Francais - Natif",
        "Anglais - Courant",
    ]
    output_path = FIXTURES_DIR / "sample_cv_bilingual.pdf"
    pdf = canvas.Canvas(str(output_path), pagesize=LETTER)
    _draw_single_column(pdf, lines)
    pdf.save()


def build_cv_multipage_pdf() -> None:
    """A CV long enough to genuinely spill onto a second PDF page - each
    experience entry is deliberately verbose so this doesn't depend on
    line-height tuning to force a page break."""
    lines = [
        "Priya Natarajan",
        "priya.natarajan@example.com | +1 650 555 0177",
        "Seattle, WA",
        "",
        "SUMMARY",
        "Staff engineer with over a decade of experience across payments and platform teams.",
        "",
        "EXPERIENCE",
    ]
    roles = [
        ("Staff Engineer", "Fulcrum Payments", "2021", "Present"),
        ("Senior Engineer", "Fulcrum Payments", "2018", "2021"),
        ("Software Engineer II", "Harbor Logistics", "2015", "2018"),
        ("Software Engineer I", "Harbor Logistics", "2013", "2015"),
    ]
    for title, company, start, end in roles:
        lines.append(f"{title}, {company}")
        lines.append(f"{start} - {end}")
        lines.append(
            "Owned a critical system end to end, partnering with product and design "
            "to ship reliable, well-tested features for millions of users."
        )
        lines.append("- Drove a major reliability initiative across the team")
        lines.append("- Reduced incident response time significantly")
        lines.append("Technologies: Python, Django, PostgreSQL, Kafka")
        lines.append("")
    lines += [
        "EDUCATION",
        "BSc Computer Science, University of Michigan",
        "2009 - 2013",
        "",
        "SKILLS",
        "Python, Django, PostgreSQL, Kafka, Docker, Kubernetes, AWS, React",
    ]
    output_path = FIXTURES_DIR / "sample_cv_multipage.pdf"
    pdf = canvas.Canvas(str(output_path), pagesize=LETTER)
    _draw_single_column(pdf, lines, line_height=18)
    pdf.save()


def build_cv_unusual_headings_pdf() -> None:
    """Uses real but less-common heading vocabulary the pre-overhaul
    taxonomy did not recognize at all (Core Qualifications, Leadership,
    Affiliations, Additional Information) - exercises the newly-added
    SectionType members end to end, not just normalize_section_heading()
    in isolation."""
    lines = [
        "Devon Clarke",
        "devon.clarke@example.com",
        "",
        "CORE QUALIFICATIONS",
        "Distributed systems, mentorship, incident response.",
        "",
        "PROFESSIONAL EXPERIENCE",
        "Engineering Lead, Fathom Data",
        "2019 - Present",
        "Runs a team of six engineers building the ingestion platform.",
        "",
        "LEADERSHIP",
        "Chaired the internal engineering guild for two years.",
        "",
        "AFFILIATIONS",
        "Member, Association for Computing Machinery",
        "",
        "ADDITIONAL INFORMATION",
        "Fluent in conversational Japanese.",
    ]
    output_path = FIXTURES_DIR / "sample_cv_unusual_headings.pdf"
    pdf = canvas.Canvas(str(output_path), pagesize=LETTER)
    _draw_single_column(pdf, lines)
    pdf.save()


def build_cv_no_headings_pdf() -> None:
    """No heading-shaped lines at all - the whole document must come
    back as a single leading SectionType.OTHER section rather than
    detect_sections misfiring on some unlucky line, and the extractor
    must still recover name/contact from it without inventing structure
    that isn't there."""
    lines = [
        "Robin Ellis",
        "robin.ellis@example.com | +1 303 555 0142",
        "Denver, CO",
        "Backend engineer with six years of experience building distributed systems",
        "and leading small teams. Comfortable across the stack from Postgres to React.",
        "Previously at Fulcrum Payments and Harbor Logistics.",
    ]
    output_path = FIXTURES_DIR / "sample_cv_no_headings.pdf"
    pdf = canvas.Canvas(str(output_path), pagesize=LETTER)
    _draw_single_column(pdf, lines)
    pdf.save()


def build_cv_varied_fonts_pdf() -> None:
    """Headings are real (larger, bold) typography rather than ALL CAPS
    or an exact alias match, so heading detection has to lean on the
    font-size/bold signals (see domain/cv/policies.py::_heading_score)
    instead of the string-only heuristics every other fixture exercises.
    "Awards Recognition" and "Getting In Touch" are deliberately *not*
    exact aliases - they only cross the heading threshold because they
    are large, bold, and short.
    """
    output_path = FIXTURES_DIR / "sample_cv_varied_fonts.pdf"
    pdf = canvas.Canvas(str(output_path), pagesize=LETTER)
    y = PAGE_HEIGHT - 50

    def heading(text: str) -> None:
        nonlocal y
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(50, y, text)
        y -= 22

    def body(text: str) -> None:
        nonlocal y
        pdf.setFont("Helvetica", 10)
        pdf.drawString(50, y, text)
        y -= 16

    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(50, y, "Harper Quinn")
    y -= 24
    body("harper.quinn@example.com")
    y -= 8

    heading("Experience")
    body("Lead Engineer, Solstice Labs")
    body("2018 - Present")
    body("Built the real-time analytics pipeline serving the whole company.")
    y -= 8

    heading("Awards Recognition")
    body("Employee of the year, 2022.")
    y -= 8

    heading("Getting In Touch")
    body("Open to remote opportunities across North America and Europe.")

    pdf.save()


def build_cv_table_docx() -> None:
    """A DOCX CV that lays out its skills as a table instead of prose -
    the pre-overhaul DOCX parser only ever read `document.paragraphs`,
    so table content was silently dropped entirely; this fixture fails
    loudly (missing skills) if that regresses."""
    output_path = FIXTURES_DIR / "sample_cv_table.docx"
    document = Document()
    document.add_paragraph("Jamie Okafor")
    document.add_paragraph("jamie.okafor@example.com")
    document.add_paragraph("")
    document.add_heading("Experience", level=1)
    document.add_paragraph("Backend Engineer, Fathom Data")
    document.add_paragraph("2020 - Present")
    document.add_paragraph("Built ingestion services for the analytics platform.")
    document.add_paragraph("")
    document.add_heading("Skills", level=1)
    table = document.add_table(rows=2, cols=3)
    values = [["Python", "Django", "PostgreSQL"], ["Docker", "Kubernetes", "AWS"]]
    for row_index, row_values in enumerate(values):
        for col_index, value in enumerate(row_values):
            table.cell(row_index, col_index).text = value
    document.save(str(output_path))


def build_cv_docx_heading_styles() -> None:
    """A DOCX CV that uses real Word "Heading" paragraph styles instead
    of relying on capitalization - exercises LineRecord.is_heading_style
    end to end (see docx_parser.py)."""
    output_path = FIXTURES_DIR / "sample_cv_heading_styles.docx"
    document = Document()
    document.add_paragraph("Nadia Hassan")
    document.add_paragraph("nadia.hassan@example.com")
    document.add_paragraph("")
    document.add_heading("Professional Experience", level=1)
    document.add_paragraph("Senior Engineer, Fathom Data")
    document.add_paragraph("2019 - Present")
    document.add_paragraph("Leads the platform reliability team.")
    document.add_paragraph("")
    document.add_heading("Technical Skills", level=1)
    document.add_paragraph("Python, Django, PostgreSQL, Docker")
    document.save(str(output_path))


if __name__ == "__main__":
    build_cv_pdf()
    build_cv_docx()
    build_job_offer_txt()
    build_job_offer_docx()
    build_corrupted_pdf()
    build_empty_pdf()
    build_unsupported_file()

    build_cv_fr_pdf()
    build_cv_fr_docx()
    build_cv_two_column_en_pdf()
    build_cv_two_column_fr_pdf()
    build_cv_bilingual_pdf()
    build_cv_multipage_pdf()
    build_cv_unusual_headings_pdf()
    build_cv_no_headings_pdf()
    build_cv_varied_fonts_pdf()
    build_cv_table_docx()
    build_cv_docx_heading_styles()

    print(f"Fixtures written to {FIXTURES_DIR}")
