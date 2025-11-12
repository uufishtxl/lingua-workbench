from rest_framework import serializers
from .models import SourceAudio, AudioChunk, AudioSlice, AudioTag, Drama

class SourceAudioSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceAudio
        fields = '__all__'
        read_only_fields = ['user', 'uploaded_at']

class AudioChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioChunk
        fields = '__all__'

class AudioSliceSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=AudioTag.objects.all(), required=False)

    class Meta:
        model = AudioSlice
        fields = '__all__'
        read_only_fields = ['file', 'created_at'] # 'file' is handled by the service, 'created_at' is auto_now_add

class DramaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Drama
        fields = '__all__'


class AudioChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioChunk
        fields = '__all__'