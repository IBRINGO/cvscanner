"""Views for the Tailoring resource (Phase 5 sections 37-39). Thin,
mirroring interfaces/api/v1/analyses/views.py exactly: validate, call an
application use case via config/container.py, serialize the result.
Never accepts a CV/job upload or re-uploads anything - a tailoring
request only ever references an already-completed `analysis_id`
(section 38).
"""
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from application.tailoring.create_tailoring_plan import TailoringValidationError
from apps.tailoring.models import TailoringPlan
from config.container import build_create_tailoring_plan
from domain.tailoring.enums import TailoringMode
from interfaces.api.v1.tailoring.serializers import (
    TailoringChangeSerializer,
    TailoringPlanDetailSerializer,
    TailoringPlanSummarySerializer,
    TailoringStatusSerializer,
)
from workers.tasks.tailoring_tasks import run_tailoring


class TailoringListCreateView(APIView):
    def get(self, request):
        plans = TailoringPlan.objects.all()
        return Response(TailoringPlanSummarySerializer(plans, many=True).data)

    def post(self, request):
        analysis_id = request.data.get("analysis_id")
        mode_value = request.data.get("mode")
        recommendation_ids = request.data.get("recommendation_ids") or []

        if not analysis_id or not mode_value:
            return Response(
                {"detail": "analysis_id and mode are required."}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            mode = TailoringMode(mode_value)
        except ValueError:
            return Response(
                {"detail": f"mode must be one of {[m.value for m in TailoringMode]}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            plan_id = build_create_tailoring_plan().execute(analysis_id, mode, recommendation_ids)
        except TailoringValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({"detail": "analysis_id does not exist."}, status=status.HTTP_404_NOT_FOUND)

        run_tailoring.delay(plan_id)

        plan_row = TailoringPlan.objects.get(id=plan_id)
        return Response(TailoringPlanSummarySerializer(plan_row).data, status=status.HTTP_202_ACCEPTED)


class TailoringDetailView(APIView):
    def get(self, request, plan_id):
        plan = get_object_or_404(TailoringPlan, id=plan_id)
        return Response(TailoringPlanDetailSerializer(plan).data)


class TailoringStatusView(APIView):
    def get(self, request, plan_id):
        plan = get_object_or_404(TailoringPlan, id=plan_id)
        return Response(TailoringStatusSerializer(plan).data)


class TailoringChangesView(APIView):
    def get(self, request, plan_id):
        plan = get_object_or_404(TailoringPlan, id=plan_id)
        return Response(TailoringChangeSerializer(plan.changes.all(), many=True).data)
