from rest_framework import serializers
from .models import PhraseLog, Tag # , SourceAudio

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']

class PhraseLogSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = PhraseLog
        # 我们告诉“翻译官”，我们想暴露哪些字段
        fields = [
            'id', 
            'original_context', 
            'expression_text', 
            'chinese_meaning', 
            'example_sentence', 
            'tags',
            'tested',
            'failed',
            'failed_radio',
            'remark',
            'created_at'
        ]
        # (我们 *不* 暴露 'user' 字段, 因为那没必要)

# class SourceAudioSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = SourceAudio
#         fields = ['id', 'title', 'file', 'uploaded_at']
#         read_only_fields = ['uploaded_at']