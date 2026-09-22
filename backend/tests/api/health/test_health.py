from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


class TestHealthEndpoint:
    def test_health_returns_200_ok(self):
        client = APIClient()
        url = reverse("health")

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_health_response_shape(self):
        client = APIClient()
        url = reverse("health")

        response = client.get(url)

        assert response.data == {
            "status": "ok",
            "service": "cvscanner-backend",
            "version": "0.1.0",
        }

    def test_health_does_not_leak_configuration(self):
        client = APIClient()
        url = reverse("health")

        response = client.get(url)

        body = str(response.data).lower()
        assert "secret" not in body
        assert "password" not in body
        assert "database" not in body
