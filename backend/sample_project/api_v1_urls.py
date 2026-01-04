from django.urls import path, include

urlpatterns = [
    # URLs from phrase_log app
    path('', include('phrase_log.urls')),
    
    # URLs from audio_slicer app
    path('', include('audio_slicer.urls')),

    path('', include('ai_analysis.urls'))
]
