"""
URL configuration for ai_analysis app.
"""
from django.urls import path
from .views import SoundScriptAnalysisView, DictionaryLookupView, RefreshExampleView

urlpatterns = [
    path('sound-script/', SoundScriptAnalysisView.as_view(), name='sound-script-analysis'),
    path('dictionary/', DictionaryLookupView.as_view(), name='dictionary-lookup'),
    path('refresh-example/', RefreshExampleView.as_view(), name='refresh-example'),
]
