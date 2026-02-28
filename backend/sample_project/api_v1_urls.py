from django.urls import path, include

urlpatterns = [
    # URLs from phrase_log app
    path('', include('phrase_log.urls')),
    
    path('', include('audio_slicer.urls')),

    path('', include('ai_analysis.urls')),
    
    # URLs from reader app
    path('', include('reader.urls')),
    
    # URLs from pomodoro app
    path('', include('pomodoro.urls'))
]
