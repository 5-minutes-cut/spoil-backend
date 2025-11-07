from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .models import Episode
from .serializers import EpisodeSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class EpisodeViewSet(viewsets.ModelViewSet):
    """
    에피소드 정보를 관리하는 ViewSet
    """
    queryset = Episode.objects.all()
    serializer_class = EpisodeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(
        operation_summary="에피소드 목록 조회",
        operation_description="모든 에피소드 목록을 반환합니다.",
        manual_parameters=[
            openapi.Parameter(
                'season',
                openapi.IN_QUERY,
                description="시즌 ID로 필터링",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={200: EpisodeSerializer(many=True)}
    )
    def list(self, request):
        queryset = self.get_queryset()
        season_id = request.query_params.get('season', None)
        if season_id:
            queryset = queryset.filter(season_id=season_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="에피소드 상세 조회",
        operation_description="특정 에피소드의 상세 정보를 조회합니다.",
        responses={
            200: EpisodeSerializer(),
            404: "에피소드를 찾을 수 없습니다."
        }
    )
    def retrieve(self, request, pk=None):
        return super().retrieve(request, pk=pk)