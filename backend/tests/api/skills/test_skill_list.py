import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestSkillList:
    def test_returns_the_seeded_taxonomy(self, api_client):
        response = api_client.get(reverse("skill-list"))

        assert response.status_code == status.HTTP_200_OK
        names = {skill["canonical_name"] for skill in response.data}
        assert "Django" in names
        assert "Python" in names

    def test_each_skill_carries_domain_and_category(self, api_client):
        response = api_client.get(reverse("skill-list"))

        django = next(skill for skill in response.data if skill["canonical_name"] == "Django")
        assert django["category"] == "FRAMEWORK"
        assert django["domain"] == "SOFTWARE_DEVELOPMENT"
        assert django["description"]
