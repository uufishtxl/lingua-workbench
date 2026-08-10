from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'textbooks', views.TextbookViewSet, basename='textbook')
router.register(r'corpus-tasks', views.CorpusTaskViewSet, basename='corpus-task')

urlpatterns = [
    path('', include(router.urls)),
    path('corpus-tasks/<int:pk>/tts-slices/', views.TtsSlicesUpdateView.as_view()),
]
