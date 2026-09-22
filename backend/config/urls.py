"""Root URL configuration.

Everything the API exposes lives under /api/v1/ — see
interfaces/api/v1/urls.py. This file intentionally stays a one-liner so
API versioning is unambiguous.
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("interfaces.api.v1.urls")),
]
