from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EpisodeViewSet

router = DefaultRouter()
router.register('', EpisodeViewSet, basename='episode')

urlpatterns = [
    path('', include(router.urls)),
]
