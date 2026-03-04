from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'authors', views.AuthorViewSet, basename='author')
router.register(r'psandboxes', views.PSandboxViewSet, basename='psandbox')

urlpatterns = [
    # Add the new router URLs to our urlpatterns
    path('', include(router.urls)),
]