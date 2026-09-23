"""Views for the Analyses resource (Phase 4 section 34). Thin, mirroring
interfaces/api/v1/cvs/views.py: parse the request, call an application
use case via config/container.py, serialize the result. Never accepts a
file upload - an analysis only ever references CV/job documents Phase 2
already ingested through their own endpoints.
"""
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analyses.models import Analysis
from config.container import build_create_analysis
from domain.matching.exceptions import AnalysisValidationError
from interfaces.api.v1.analyses.serializers import (
    AnalysisDetailSerializer,
    AnalysisStatusSerializer,
    AnalysisSummarySerializer,
)
from workers.tasks.analysis_tasks import run_analysis


class AnalysisListCreateView(APIView):
    def get(self, request):
        analyses = Analysis.objects.all()
        return Response(AnalysisSummarySerializer(analyses, many=True).data)

    def post(self, request):
        candidate_document_id = request.data.get("candidate_document_id")
        job_document_id = request.data.get("job_document_id")
        if not candidate_document_id or not job_document_id:
            return Response(
                {"detail": "Both candidate_document_id and job_document_id are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            analysis_id = build_create_analysis().execute(candidate_document_id, job_document_id)
        except AnalysisValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response(
                {"detail": "candidate_document_id or job_document_id does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        run_analysis.delay(analysis_id)

        analysis_row = Analysis.objects.get(id=analysis_id)
        return Response(AnalysisSummarySerializer(analysis_row).data, status=status.HTTP_202_ACCEPTED)


class AnalysisDetailView(APIView):
    def get(self, request, analysis_id):
        analysis = get_object_or_404(Analysis, id=analysis_id)
        return Response(AnalysisDetailSerializer(analysis).data)


class AnalysisStatusView(APIView):
    def get(self, request, analysis_id):
        analysis = get_object_or_404(Analysis, id=analysis_id)
        return Response(AnalysisStatusSerializer(analysis).data)
