from rest_framework import serializers
from .models import SourceAudio

class SourceAudioSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceAudio
        fields = '__all__'
        read_only_fields = ['uploaded_at']

