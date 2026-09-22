import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestSkillDetail:
    def test_returns_parent_and_children(self, api_client):
        response = api_client.get(reverse("skill-detail", args=["Django"]))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["parent"]["canonical_name"] == "Python"
        child_names = {child["canonical_name"] for child in response.data["children"]}
        assert "Django REST Framework" in child_names

    def test_returns_ecosystem_siblings(self, api_client):
        response = api_client.get(reverse("skill-detail", args=["Django"]))

        sibling_names = {sibling["canonical_name"] for sibling in response.data["ecosystem_siblings"]}
        assert "Flask" in sibling_names
        assert "Django" not in sibling_names

    def test_returns_explicit_alternative_relations(self, api_client):
        response = api_client.get(reverse("skill-detail", args=["Django"]))

        alternatives = {
            related["skill"]["canonical_name"]
            for related in response.data["explicit"]
            if related["relation_type"] == "ALTERNATIVE_TO"
        }
        assert "Flask" in alternatives
        assert "FastAPI" in alternatives

    def test_relationship_never_implies_equivalence(self, api_client):
        response = api_client.get(reverse("skill-detail", args=["Django"]))

        assert response.data["canonical_name"] == "Django"
        assert response.data["parent"]["canonical_name"] != "Django"

    def test_unknown_skill_returns_404(self, api_client):
        response = api_client.get(reverse("skill-detail", args=["Nonexistent Skill"]))
        assert response.status_code == status.HTTP_404_NOT_FOUND
