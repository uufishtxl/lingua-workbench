from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PomodoroTagViewSet, PomodoroViewSet

router = DefaultRouter()
router.register(r'pomodoro-tags', PomodoroTagViewSet, basename='pomodoro-tag')
router.register(r'pomodoros', PomodoroViewSet, basename='pomodoro')

app_name = 'pomodoro'

urlpatterns = [
    path('', include(router.urls)),
]
