from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .models import Season
from .serializers import SeasonSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class SeasonViewSet(viewsets.ModelViewSet):
    """
    시즌 정보를 관리하는 ViewSet
    """
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(
        operation_summary="시즌 목록 조회",
        operation_description="모든 시즌 목록을 반환합니다.",
        manual_parameters=[
            openapi.Parameter(
                'series',
                openapi.IN_QUERY,
                description="시리즈 ID로 필터링",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={200: SeasonSerializer(many=True)}
    )
    def list(self, request):
        queryset = self.get_queryset()
        series_id = request.query_params.get('series', None)
        if series_id:
            queryset = queryset.filter(series_id=series_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="시즌 상세 조회",
        operation_description="특정 시즌의 상세 정보를 조회합니다.",
        responses={
            200: SeasonSerializer(),
            404: "시즌을 찾을 수 없습니다."
        }
    )
    def retrieve(self, request, pk=None):
        return super().retrieve(request, pk=pk)
