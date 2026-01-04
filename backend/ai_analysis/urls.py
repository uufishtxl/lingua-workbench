"""
URL configuration for ai_analysis app.
"""
from django.urls import path
from .views import SoundScriptAnalysisView

urlpatterns = [
    path('sound-script/', SoundScriptAnalysisView.as_view(), name='sound-script-analysis'),
]
