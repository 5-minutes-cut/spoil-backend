from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .models import Series
from .serializers import SeriesSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class SeriesViewSet(viewsets.ModelViewSet):
    """
    시리즈(애니메이션) 정보를 관리하는 ViewSet
    """
    queryset = Series.objects.all()
    serializer_class = SeriesSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(
        operation_summary="시리즈 목록 조회",
        operation_description="등록된 모든 시리즈(애니메이션) 목록을 반환합니다.",
        responses={200: SeriesSerializer(many=True)}
    )
    def list(self, request):
        return super().list(request)

    @swagger_auto_schema(
        operation_summary="시리즈 상세 조회",
        operation_description="특정 시리즈의 상세 정보를 조회합니다.",
        responses={
            200: SeriesSerializer(),
            404: "시리즈를 찾을 수 없습니다."
        }
    )
    def retrieve(self, request, pk=None):
        return super().retrieve(request, pk=pk)