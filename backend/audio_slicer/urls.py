from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'audios', views.SourceAudioViewSet, basename='sourceaudio')

urlpatterns = [
    # Add the new router URLs to our urlpatterns
    path('', include(router.urls)),
]