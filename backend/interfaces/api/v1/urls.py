"""URL routing for API v1.

Only `health/` exists in Phase 1. Future resources (auth, cvs, jobs,
analyses, recommendations, tailoring) each get their own
`interfaces/api/v1/<resource>/urls.py` included here, following the same
pattern.
"""
from django.urls import include, path

urlpatterns = [
    path("health/", include("interfaces.api.v1.health.urls")),
]
