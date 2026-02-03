from rest_framework import serializers
from .models import SourceAudio, AudioChunk, AudioSlice, Drama, ReviewCard

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
        fields = ['id', 'audio_chunk', 'start_time', 'end_time', 'original_text', 
                  'translation', 'highlights', 'is_pronunciation_hard', 'is_idiom', 
                  'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
        # Disable unique_together validators - we use update_or_create in batch view
        validators = []

class DramaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Drama
        fields = '__all__'
        read_only_fields = ['user']

class ReviewCardSerializer(serializers.ModelSerializer):
    slice_text = serializers.CharField(source='audio_slice.original_text', read_only=True)
    slice_translation = serializers.CharField(source='audio_slice.translation', read_only=True)
    audio_url = serializers.FileField(source='audio_slice.audio_chunk.file', read_only=True)
    start_time = serializers.FloatField(source='audio_slice.start_time', read_only=True)
    end_time = serializers.FloatField(source='audio_slice.end_time', read_only=True)

    class Meta:
        model = ReviewCard
        fields = ['id', 'box_level', 'next_review_date', 'last_reviewed_at', 'review_type', 
                  'slice_text', 'slice_translation', 'audio_url', 'start_time', 'end_time', 'audio_slice']
        read_only_fields = ['box_level', 'next_review_date', 'last_reviewed_at', 'review_type', 'audio_slice']