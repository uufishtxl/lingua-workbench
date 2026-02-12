from rest_framework import serializers
from .models import ScriptLine


class ScriptLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScriptLine
        fields = [
            'id',
            'chunk',
            'index',
            'line_type',
            'speaker',
            'text',
            'action_note',
            'raw_text',
            'slice',
            'highlight',
        ]
        read_only_fields = ['id', 'raw_text']


class ScriptLineListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list view (excludes raw_text)."""
    class Meta:
        model = ScriptLine
        fields = [
            'id',
            'index',
            'line_type',
            'speaker',
            'text',
            'text_zh',
            'action_note',
            'slice',
            'highlight',
        ]


class SplitRequestSerializer(serializers.Serializer):
    start_index = serializers.IntegerField(min_value=0)
    next_chunk_id = serializers.IntegerField()


class IngestRequestSerializer(serializers.Serializer):
    season = serializers.IntegerField(min_value=1, max_value=10)
    episode = serializers.IntegerField(min_value=1)


class BlitzCardSerializer(serializers.ModelSerializer):
    """
    Serializer for Blitz Camp cards.
    """
    id = serializers.IntegerField(read_only=True)  # Keeping 'id' for frontend key
    script_id = serializers.IntegerField(source='id', read_only=True)
    episode = serializers.SerializerMethodField()
    chunk_id = serializers.IntegerField(source='chunk.id', read_only=True)
    order = serializers.IntegerField(source='index', read_only=True)
    content = serializers.SerializerMethodField()
    
    class Meta:
        model = ScriptLine
        fields = [
            'id',
            'script_id',
            'episode',
            'chunk_id',
            'order',
            'speaker',
            'content',
            'highlight',
        ]
    
    def get_episode(self, obj):
        # e.g. "S10E12"
        if obj.chunk and obj.chunk.source_audio:
            sa = obj.chunk.source_audio
            return f"S{sa.season}E{str(sa.episode).zfill(2)}"
        return "Unknown"

    def get_content(self, obj):
        audio_url = None
        if obj.chunk and obj.chunk.file:
            request = self.context.get('request')
            if request:
                audio_url = request.build_absolute_uri(obj.chunk.file.url)
            else:
                audio_url = obj.chunk.file.url
                
        return {
            "text_zh": obj.text_zh,
            "text": obj.text,
            "audio_url": audio_url,
            # Pass timing for slicing if needed by frontend, though usually pre-sliced
            "start_time": obj.slice.start_time if obj.slice else None,
            "end_time": obj.slice.end_time if obj.slice else None,
        }
