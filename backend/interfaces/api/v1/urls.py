"""URL routing for API v1.

Each resource gets its own `interfaces/api/v1/<resource>/urls.py`
included here. Future resources (auth, analyses, recommendations,
tailoring) follow the same pattern.
"""
from django.urls import include, path

urlpatterns = [
    path("health/", include("interfaces.api.v1.health.urls")),
    path("cvs/", include("interfaces.api.v1.cvs.urls")),
    path("jobs/", include("interfaces.api.v1.jobs.urls")),
    path("skills/", include("interfaces.api.v1.skills.urls")),
]
