from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SeriesViewSet

router = DefaultRouter()
router.register('', SeriesViewSet, basename='series')

urlpatterns = [
    path('', include(router.urls)),
]
