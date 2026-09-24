"""End-to-end coverage for the document-intelligence overhaul: real
fixture bytes through the real Celery-eager pipeline (parse -> language
detection -> layout-aware section detection -> extraction -> persistence
-> API response), exercising French, two-column, and DOCX-table CVs the
pre-overhaul pipeline could not handle correctly. See tests/fixtures/
generate_fixtures.py for what each fixture specifically represents.
"""
import pytest
from django.urls import reverse
from rest_framework import status

from tests.api.cvs.conftest import make_upload


def _upload_and_get_profile(api_client, filename: str, content: bytes, content_type: str) -> dict:
    upload = api_client.post(
        reverse("cv-list-create"),
        {"file": make_upload(filename, content, content_type)},
        format="multipart",
    )
    assert upload.status_code == status.HTTP_202_ACCEPTED, upload.data
    response = api_client.get(reverse("cv-profile", args=[upload.data["id"]]))
    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "PROCESSED", response.data
    return response.data["profile"]


@pytest.mark.django_db
class TestFrenchCvEndToEnd:
    def test_french_pdf_is_extracted_correctly_through_the_real_pipeline(self, fixture_bytes, api_client):
        profile = _upload_and_get_profile(
            api_client, "sample_cv_fr.pdf", fixture_bytes("sample_cv_fr.pdf"), "application/pdf"
        )

        assert profile["full_name"] == "Camille Dubois"
        assert profile["email"] == "camille.dubois@example.fr"
        assert profile["location"] == "Paris, France"
        assert len(profile["experiences"]) == 2
        first = profile["experiences"][0]
        assert first["company"] == "Meridian Analytics"
        assert first["start_date_raw"] == "Janvier 2020"
        assert first["is_current"] is True
        assert profile["education"][0]["institution"] == "Universite de Paris"
        skill_names = {s["raw_text"] for s in profile["skills"]}
        assert {"Python", "Django"} <= skill_names

    def test_french_docx_is_extracted_correctly_through_the_real_pipeline(self, fixture_bytes, api_client):
        profile = _upload_and_get_profile(
            api_client,
            "sample_cv_fr.docx",
            fixture_bytes("sample_cv_fr.docx"),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        assert profile["full_name"] == "Camille Dubois"
        assert len(profile["experiences"]) == 2


@pytest.mark.django_db
class TestTwoColumnCvEndToEnd:
    def test_two_column_english_cv_never_interleaves_columns(self, fixture_bytes, api_client):
        profile = _upload_and_get_profile(
            api_client,
            "sample_cv_two_column_en.pdf",
            fixture_bytes("sample_cv_two_column_en.pdf"),
            "application/pdf",
        )

        assert profile["full_name"] == "Taylor Morgan"
        skill_names = {s["raw_text"] for s in profile["skills"]}
        assert {"Python", "Django", "Kubernetes"} <= skill_names
        assert len(profile["certifications"]) == 1
        assert profile["certifications"][0]["name"] == "AWS Certified Developer"

        assert len(profile["experiences"]) == 2
        first = profile["experiences"][0]
        assert first["title"] == "Senior Platform Engineer"
        assert first["company"] == "Beacon Systems"
        # The strongest possible regression check: none of the left
        # column's skill tokens leaked into the right column's
        # experience description, which is exactly what an interleaved
        # (wrong) reading order would produce.
        for skill in ("Python", "Django", "PostgreSQL", "Docker", "Kubernetes", "Git"):
            assert skill not in (first["description"] or "")

    def test_two_column_french_cv_never_interleaves_columns(self, fixture_bytes, api_client):
        profile = _upload_and_get_profile(
            api_client,
            "sample_cv_two_column_fr.pdf",
            fixture_bytes("sample_cv_two_column_fr.pdf"),
            "application/pdf",
        )

        assert profile["full_name"] == "Sacha Bernard"
        assert len(profile["experiences"]) == 2
        assert profile["experiences"][0]["company"] == "Beacon Systems"


@pytest.mark.django_db
class TestOtherOverhaulScenarios:
    def test_multipage_cv_extracts_all_experience_entries_across_pages(self, fixture_bytes, api_client):
        profile = _upload_and_get_profile(
            api_client, "sample_cv_multipage.pdf", fixture_bytes("sample_cv_multipage.pdf"), "application/pdf"
        )
        assert len(profile["experiences"]) == 4

    def test_docx_table_content_reaches_the_final_profile(self, fixture_bytes, api_client):
        profile = _upload_and_get_profile(
            api_client,
            "sample_cv_table.docx",
            fixture_bytes("sample_cv_table.docx"),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        skill_names = {s["raw_text"] for s in profile["skills"]}
        assert {"Python", "Django", "PostgreSQL", "Docker", "Kubernetes", "AWS"} <= skill_names

    def test_cv_with_no_headings_still_recovers_name_and_contact_without_inventing_sections(
        self, fixture_bytes, api_client
    ):
        profile = _upload_and_get_profile(
            api_client,
            "sample_cv_no_headings.pdf",
            fixture_bytes("sample_cv_no_headings.pdf"),
            "application/pdf",
        )
        assert profile["full_name"] == "Robin Ellis"
        assert profile["email"] == "robin.ellis@example.com"
        assert profile["experiences"] == []
        assert profile["skills"] == []

    def test_unusual_heading_vocabulary_does_not_get_dropped_or_merged(self, fixture_bytes, api_client):
        # Confirms the new SectionType members are actually reachable
        # through the full pipeline, not just normalize_section_heading()
        # in isolation - a real assertion is only possible on fields the
        # CandidateProfile API already exposes (full_name, experiences),
        # so this checks the leadership/affiliations text didn't bleed
        # into the Experience entry that precedes it.
        profile = _upload_and_get_profile(
            api_client,
            "sample_cv_unusual_headings.pdf",
            fixture_bytes("sample_cv_unusual_headings.pdf"),
            "application/pdf",
        )
        assert profile["full_name"] == "Devon Clarke"
        assert len(profile["experiences"]) == 1
        description = profile["experiences"][0]["description"] or ""
        assert "Chaired the internal engineering guild" not in description
        assert "Association for Computing Machinery" not in description
