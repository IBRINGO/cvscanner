"""Liveness/readiness endpoint.

Kept intentionally simple for Phase 1: it proves the API process is up and
can respond to JSON requests. It does not (yet) check database/broker
connectivity — see the module docstring in urls.py for why that
distinction matters once dependency checks are added.
"""
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

SERVICE_NAME = "cvscanner-backend"
SERVICE_VERSION = "0.1.0"


class HealthView(APIView):
    """GET /api/v1/health/ — always returns 200 while the process is alive."""

    def get(self, request: Request) -> Response:
        return Response(
            {
                "status": "ok",
                "service": SERVICE_NAME,
                "version": SERVICE_VERSION,
            }
        )
