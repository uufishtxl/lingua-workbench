import os
import subprocess # No longer directly used for ffmpeg here, but might be for other things
import tempfile # No longer directly used for tempdir here
from pathlib import Path # No longer directly used here

from django.core.files import File # No longer directly used here
from rest_framework import viewsets, parsers, serializers
from rest_framework.permissions import IsAuthenticated

from .models import SourceAudio, AudioChunk
from .serializers import SourceAudioSerializer
from .services import slice_source_to_chunks # Import the new service function

class SourceAudioViewSet(viewsets.ModelViewSet):
    """
    API endpoint for uploading and managing source audio files.
    Triggers ffmpeg segmentation on upload.
    """
    queryset = SourceAudio.objects.all()
    serializer_class = SourceAudioSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def perform_create(self, serializer):
        # First, save the SourceAudio instance to get an ID and file path
        # We also associate the currently authenticated user.
        serializer.save(user=self.request.user)


