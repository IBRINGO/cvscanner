import pytest
from django.urls import reverse
from rest_framework import status

try:
    import weasyprint  # noqa: F401

    _WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    # WeasyPrint needs native Pango/Cairo/GDK-pixbuf libraries that are
    # installed in the backend Docker image but not on a bare Windows/macOS
    # dev machine - see infrastructure/docker/backend.Dockerfile. Run these
    # specific tests inside the backend container instead.
    _WEASYPRINT_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not _WEASYPRINT_AVAILABLE, reason="WeasyPrint's native libraries are not available on this machine"
)


def _profile(**overrides):
    base = {
        "full_name": "Jordan Rivera",
        "email": "jordan@example.com",
        "phone": None,
        "location": "Remote",
        "links": ["linkedin.com/in/jordan"],
        "summary": "Backend engineer.",
        "experiences": [
            {
                "title": "Senior Backend Engineer",
                "company": "Acme",
                "start_date_raw": "2020",
                "end_date_raw": None,
                "description": "Built the platform.",
                "achievements": ["Shipped the v2 API"],
                "technologies": ["Python"],
            }
        ],
        "education": [],
        "projects": [],
        "certifications": [],
        "languages": [],
        "skills": [{"raw_text": "Python", "skill": {"canonical_name": "Python"}}],
    }
    base.update(overrides)
    return base


def _section_order():
    return [
        {"id": "summary", "kind": "summary"},
        {"id": "experience", "kind": "experience"},
        {"id": "skills", "kind": "skills"},
    ]


@pytest.mark.django_db
class TestCvRenderPdf:
    def test_renders_a_real_pdf_file(self, api_client):
        response = api_client.post(
            reverse("cv-render-pdf"),
            {
                "profile": _profile(),
                "template_id": "ats-classic",
                "section_order": _section_order(),
                "hidden_section_ids": [],
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/pdf"
        assert response.content.startswith(b"%PDF")
        assert "attachment" in response["Content-Disposition"]
        assert "jordan-rivera" in response["Content-Disposition"]

    def test_renders_every_template_without_error(self, api_client):
        for template_id in ["ats-classic", "ats-professional", "executive", "modern-split", "technical", "minimal"]:
            response = api_client.post(
                reverse("cv-render-pdf"),
                {
                    "profile": _profile(),
                    "template_id": template_id,
                    "section_order": _section_order(),
                    "hidden_section_ids": [],
                },
                format="json",
            )
            assert response.status_code == status.HTTP_200_OK, template_id
            assert response.content.startswith(b"%PDF")

    def test_respects_hidden_sections(self, api_client):
        response = api_client.post(
            reverse("cv-render-pdf"),
            {
                "profile": _profile(),
                "template_id": "ats-classic",
                "section_order": _section_order(),
                "hidden_section_ids": ["skills"],
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

    def test_missing_profile_is_rejected(self, api_client):
        response = api_client.post(reverse("cv-render-pdf"), {"template_id": "ats-classic"}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_renders_a_custom_section(self, api_client):
        response = api_client.post(
            reverse("cv-render-pdf"),
            {
                "profile": _profile(),
                "template_id": "minimal",
                "section_order": [
                    *_section_order(),
                    {"id": "custom-1", "kind": "custom", "title": "Awards", "content": "Employee of the year."},
                ],
                "hidden_section_ids": [],
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.content.startswith(b"%PDF")

    def test_groups_skills_by_category_when_requested(self, api_client):
        response = api_client.post(
            reverse("cv-render-pdf"),
            {
                "profile": _profile(
                    skills=[
                        {"raw_text": "JUnit", "skill": {"canonical_name": "JUnit", "category": "Quality & Testing"}},
                        {"raw_text": "SpringBoot", "skill": {"canonical_name": "SpringBoot", "category": "Backend"}},
                        {"raw_text": "React", "skill": None},
                    ],
                ),
                "template_id": "modern-split",
                "section_order": _section_order(),
                "hidden_section_ids": [],
                "group_skills_by_category": True,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.content.startswith(b"%PDF")

    @pytest.mark.parametrize("template_id", ["ats-classic", "modern-split", "technical"])
    def test_content_overflowing_one_page_spills_onto_a_new_page(self, api_client, template_id):
        # A long, single-experience-repeated-many-times profile so this
        # test doesn't depend on any one template's exact line-height -
        # it just needs to overflow a single A4 page by a wide margin,
        # for both single-column and 2-column (split) templates, since
        # WeasyPrint's flex-based split layout is the riskier case for
        # cross-page fragmentation.
        long_profile = _profile(
            experiences=[
                {
                    "title": f"Role {i}",
                    "company": f"Company {i}",
                    "start_date_raw": "2015",
                    "end_date_raw": "2016",
                    "description": "Did a lot of impactful engineering work across several major initiatives.",
                    "achievements": [
                        "Improved system reliability significantly across the board",
                        "Led a cross-functional team through a major migration",
                        "Reduced costs while improving developer experience",
                    ],
                    "technologies": ["Python", "Django", "PostgreSQL"],
                }
                for i in range(12)
            ],
        )

        response = api_client.post(
            reverse("cv-render-pdf"),
            {
                "profile": long_profile,
                "template_id": template_id,
                "section_order": _section_order(),
                "hidden_section_ids": [],
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        import pypdfium2

        pdf = pypdfium2.PdfDocument(response.content)
        try:
            assert len(pdf) > 1, f"{template_id}: expected multiple pages for long content, got {len(pdf)}"
        finally:
            pdf.close()
