from rest_framework import serializers
from .models import SourceAudio, AudioChunk, AudioSlice, Drama

class SourceAudioSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceAudio
        fields = '__all__'
        read_only_fields = ['user', 'uploaded_at']

class AudioChunkSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='source_audio.title', read_only=True)
    drama = serializers.CharField(source='source_audio.drama.name', read_only=True)

    class Meta:
        model = AudioChunk
        fields = ['id', 'source_audio', 'chunk_index', 'file', 'has_slices', 'title', 'drama']

class AudioSliceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioSlice
        fields = ['id', 'audio_chunk', 'start_time', 'end_time', 'original_text', 'highlights', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class DramaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Drama
        fields = '__all__'
        read_only_fields = ['user']