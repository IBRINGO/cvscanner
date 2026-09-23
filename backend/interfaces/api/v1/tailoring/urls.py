from django.urls import path

from interfaces.api.v1.tailoring.views import (
    TailoringChangesView,
    TailoringDetailView,
    TailoringListCreateView,
    TailoringStatusView,
)

urlpatterns = [
    path("", TailoringListCreateView.as_view(), name="tailoring-list-create"),
    path("<uuid:plan_id>/", TailoringDetailView.as_view(), name="tailoring-detail"),
    path("<uuid:plan_id>/status/", TailoringStatusView.as_view(), name="tailoring-status"),
    path("<uuid:plan_id>/changes/", TailoringChangesView.as_view(), name="tailoring-changes"),
]
