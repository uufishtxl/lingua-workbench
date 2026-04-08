from django.urls import path, include

from english_corner.daily_phrases_views import (
    DailyPhrasesInitView,
    DailyPhrasesVerifyView,
    RefreshBonusView,
)

urlpatterns = [
    # URLs from phrase_log app
    path('', include('phrase_log.urls')),
    
    path('', include('audio_slicer.urls')),

    path('', include('ai_analysis.urls')),
    
    # URLs from reader app
    path('', include('reader.urls')),
    
    # URLs from pomodoro app
    path('', include('pomodoro.urls')),
    
    # URLs from english_corner app
    path('english_corner/', include('english_corner.urls')),

    # Daily Phrases (mounted at /api/v1/daily-phrases/...)
    path('daily-phrases/init/', DailyPhrasesInitView.as_view(), name='daily-phrases-init'),
    path('daily-phrases/verify/', DailyPhrasesVerifyView.as_view(), name='daily-phrases-verify'),
    path('daily-phrases/refresh-bonus/', RefreshBonusView.as_view(), name='daily-phrases-refresh-bonus'),
]

