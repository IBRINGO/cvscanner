"""View for the Recommendations resource (Phase 5 section 37: `GET
/api/v1/analyses/{id}/recommendations/`). Thin, mirroring
interfaces/api/v1/analyses/views.py: validate, call an application use
case via config/container.py, serialize the result.
"""
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analyses.models import Analysis
from apps.recommendations.models import Recommendation
from config.container import build_generate_recommendations
from domain.matching.enums import AnalysisStatus
from interfaces.api.v1.recommendations.serializers import RecommendationSerializer


class AnalysisRecommendationsView(APIView):
    def get(self, request, analysis_id):
        try:
            analysis = Analysis.objects.only("status").get(id=analysis_id)
        except ObjectDoesNotExist:
            return Response({"detail": "Analysis not found."}, status=status.HTTP_404_NOT_FOUND)

        if analysis.status != AnalysisStatus.COMPLETED.value:
            return Response(
                {"detail": "Recommendations are only available once the analysis has completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        build_generate_recommendations().execute(str(analysis_id))
        rows = Recommendation.objects.filter(analysis_id=analysis_id).order_by("id")
        return Response(RecommendationSerializer(rows, many=True).data)
