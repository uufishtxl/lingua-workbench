from rest_framework import serializers
from .models import (
    Scenario, Conversation, PracticeMessage,
    PracticeFlashcard, WordNode, WordLink,
)


class ScenarioSerializer(serializers.ModelSerializer):
    dialogue_rounds = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Scenario
        fields = [
            'id', 'title', 'description', 'icon',
            'system_prompt', 'is_preset', 'created_at',
            'dialogue_rounds'
        ]
        read_only_fields = ['system_prompt', 'created_at']


class PracticeMessageSerializer(serializers.ModelSerializer):
    """
    契约字段映射:
      - tutor_feedback: {"polished_text", "explanation_cn"} (仅 User 消息)
      - character_reply: {"content", "audio_url"} (仅 Assistant 消息)
    """
    tutor_feedback = serializers.SerializerMethodField()
    character_reply = serializers.SerializerMethodField()
    timestamp = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = PracticeMessage
        fields = [
            'id', 'role', 'status', 'is_processed', 'timestamp',
            'user_content', 'tutor_feedback', 'character_reply',
        ]

    def get_tutor_feedback(self, obj):
        if obj.role != PracticeMessage.Role.USER:
            return None
        if not obj.tutor_polished_text:
            return None
        return {
            "polished_text": obj.tutor_polished_text,
            "explanation_cn": obj.tutor_explanation_cn,
        }

    def get_character_reply(self, obj):
        if obj.role != PracticeMessage.Role.ASSISTANT:
            return None
        return {
            "content": obj.character_content,
            "audio_url": obj.audio_url if obj.audio_url else None,
        }


class ConversationSerializer(serializers.ModelSerializer):
    scenario_title = serializers.CharField(source='scenario.title', read_only=True)
    scenario_icon = serializers.CharField(source='scenario.icon', read_only=True)

    class Meta:
        model = Conversation
        fields = [
            'id', 'scenario', 'scenario_title', 'scenario_icon',
            'summary', 'is_active', 'created_at',
        ]
        read_only_fields = ['summary', 'is_active', 'created_at']


class ConversationDetailSerializer(serializers.ModelSerializer):
    """GET /conversations/{id}/ — includes recent messages."""
    messages = PracticeMessageSerializer(many=True, read_only=True)
    scenario_title = serializers.CharField(source='scenario.title', read_only=True)
    scenario_icon = serializers.CharField(source='scenario.icon', read_only=True)

    class Meta:
        model = Conversation
        fields = [
            'id', 'scenario', 'scenario_title', 'scenario_icon',
            'summary', 'is_active', 'messages', 'created_at',
        ]

    def to_representation(self, instance):
        """Only include recent messages (last 10) for the detail view."""
        data = super().to_representation(instance)
        # The messages queryset is already ordered by created_at (model Meta)
        # Slice to last 10 for the response
        messages = instance.messages.all().order_by('-created_at')[:10]
        messages = list(reversed(messages))  # Back to chronological
        data['messages'] = PracticeMessageSerializer(messages, many=True).data
        return data


class PracticeFlashcardSerializer(serializers.ModelSerializer):
    class Meta:
        model = PracticeFlashcard
        fields = [
            'id', 'target_phrase', 'prompt_question', 'answer',
            'example_context', 'box_level', 'next_review_at', 'created_at',
        ]
        read_only_fields = ['created_at']


class WordNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WordNode
        fields = [
            'id', 'label', 'node_type', 'explanation', 'example',
            'status', 'mastery', 'box_level',
        ]


class WordLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = WordLink
        fields = [
            'source_type', 'source_id',
            'target_type', 'target_id', 'relation',
        ]


class DailyPhrasesVerifySerializer(serializers.Serializer):
    word_id = serializers.IntegerField()
    user_sentence = serializers.CharField(trim_whitespace=True)
    active_bonus_words = serializers.ListField(child=serializers.DictField(), required=False)
