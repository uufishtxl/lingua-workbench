from rest_framework import serializers
from .models import (
    Scenario, Conversation, PracticeMessage,
    PracticeFlashcard, WordNode, WordOccurrence, WordLink,
)


class ScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scenario
        fields = ['id', 'title', 'description', 'icon', 'is_preset', 'created_at']


class PracticeMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PracticeMessage
        fields = [
            'id', 'role', 'user_content', 'tutor_polished_text',
            'tutor_explanation_cn', 'character_content', 'created_at'
        ]


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = [
            'id', 'scenario', 'user', 'summary', 'is_active', 'created_at'
        ]


class ConversationDetailSerializer(serializers.ModelSerializer):
    messages = PracticeMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = [
            'id', 'scenario', 'user',
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
            'id', 'label', 'tag', 'node_type', 'explanation', 'example',
            'status', 'mastery', 'box_level',
        ]


class WordOccurrenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WordOccurrence
        fields = [
            'id', 'word', 'exact_sentence', 
            'content_type', 'object_id', 'created_at'
        ]


class WordLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = WordLink
        fields = [
            'id', 'source_word', 'target_word', 'relation', 'created_at'
        ]


class DailyPhrasesVerifySerializer(serializers.Serializer):
    word_id = serializers.IntegerField()
    user_sentence = serializers.CharField(trim_whitespace=True)
    active_bonus_words = serializers.ListField(child=serializers.DictField(), required=False)
