from rest_framework import serializers
from .models import PhraseLog

class PhraseLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhraseLog
        # 我们告诉“翻译官”，我们想暴露哪些字段
        fields = [
            'id', 
            'original_content', 
            'expression_text', 
            'chinese_meaning', 
            'example_sentence', 
            'tags',
            'tested',
            'failed',
            'created_at'
        ]
        # (我们 *不* 暴露 'user' 字段, 因为那没必要)