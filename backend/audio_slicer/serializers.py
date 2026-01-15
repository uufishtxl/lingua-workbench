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
        fields = ['id', 'audio_chunk', 'start_time', 'end_time', 'original_text', 'highlights', 'is_pronunciation_hard', 'is_idiom', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
        # Disable unique_together validators - we use update_or_create in batch view
        validators = []

class DramaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Drama
        fields = '__all__'
        read_only_fields = ['user']