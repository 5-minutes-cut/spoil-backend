from rest_framework import viewsets, permissions
from .models import Genre
from .serializers import GenreSerializer
from drf_yasg.utils import swagger_auto_schema


class GenreViewSet(viewsets.ReadOnlyModelViewSet):
	"""장르 조회 전용 ViewSet"""
	queryset = Genre.objects.all()
	serializer_class = GenreSerializer
	permission_classes = [permissions.AllowAny]

	@swagger_auto_schema(
		operation_summary="장르 목록 조회",
		operation_description="모든 장르를 반환합니다.",
		responses={200: GenreSerializer(many=True)}
	)
	def list(self, request):
		return super().list(request)

	@swagger_auto_schema(
		operation_summary="장르 상세 조회",
		operation_description="특정 장르의 상세 정보를 조회합니다.",
		responses={200: GenreSerializer(), 404: '장르를 찾을 수 없습니다.'}
	)
	def retrieve(self, request, pk=None):
		return super().retrieve(request, pk=pk)
