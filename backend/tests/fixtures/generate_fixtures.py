"""Regenerates the synthetic test fixtures in this directory.

Not part of the test suite itself (pytest's `test_*.py` collection rule
skips it) - run manually when a fixture needs to change:

    python tests/fixtures/generate_fixtures.py

All content is synthetic (a fictional candidate and a fictional job
offer) - see section 55 of the Phase 2 brief ("no real people's private
CVs"). Requires `reportlab` (dev-only dependency, see pyproject.toml).
"""
from pathlib import Path

from docx import Document
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

FIXTURES_DIR = Path(__file__).parent

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


def build_cv_pdf() -> None:
    output_path = FIXTURES_DIR / "sample_cv.pdf"
    pdf = canvas.Canvas(str(output_path), pagesize=LETTER)
    _, height = LETTER
    y = height - 50
    for line in CV_LINES:
        pdf.drawString(50, y, line)
        y -= 16
        if y < 50:
            pdf.showPage()
            y = height - 50
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


if __name__ == "__main__":
    build_cv_pdf()
    build_cv_docx()
    build_job_offer_txt()
    build_job_offer_docx()
    build_corrupted_pdf()
    build_empty_pdf()
    build_unsupported_file()
    print(f"Fixtures written to {FIXTURES_DIR}")
