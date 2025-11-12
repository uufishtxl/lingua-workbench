from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'audios', views.SourceAudioViewSet, basename='sourceaudio')
router.register(r'audioslices', views.AudioSliceViewSet, basename='audioslice')
router.register(r'dramas', views.DramaViewSet, basename='drama')
router.register(r'audiochunks', views.AudioChunkViewSet, basename='audiochunks')

urlpatterns = [
    # Add the new router URLs to our urlpatterns
    path('', include(router.urls)),
]