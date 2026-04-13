from django.contrib import admin
from .models import (
    Scenario, Conversation, PracticeMessage,
    PracticeFlashcard, WordNode, WordOccurrence, WordLink, DailyPracticeLog
)


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ('title', 'icon', 'is_preset', 'user', 'created_at')
    list_filter = ('is_preset',)
    search_fields = ('title', 'description')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('user', 'scenario', 'is_active', 'created_at')
    list_filter = ('is_active', 'scenario')


@admin.register(PracticeMessage)
class PracticeMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'role', 'status', 'is_processed', 'content_preview', 'created_at')
    list_filter = ('role', 'status', 'is_processed')

    def content_preview(self, obj):
        text = obj.user_content or obj.character_content
        return text[:60] + '...' if len(text) > 60 else text
    content_preview.short_description = 'Content'


@admin.register(PracticeFlashcard)
class PracticeFlashcardAdmin(admin.ModelAdmin):
    list_display = ('target_phrase', 'user', 'box_level', 'next_review_at', 'created_at')
    list_filter = ('box_level',)
    search_fields = ('target_phrase',)


@admin.register(WordNode)
class WordNodeAdmin(admin.ModelAdmin):
    list_display = ('label', 'tag', 'node_type', 'status', 'user', 'mastery', 'box_level')
    search_fields = ('label', 'explanation')
    list_filter = ('tag', 'node_type', 'status', 'box_level')


@admin.register(WordOccurrence)
class WordOccurrenceAdmin(admin.ModelAdmin):
    list_display = ('word', 'exact_sentence', 'content_type', 'object_id')

@admin.register(WordLink)
class WordLinkAdmin(admin.ModelAdmin):
    list_display = ('user', 'source_word', 'target_word', 'relation')

@admin.register(DailyPracticeLog)
class DailyPracticeLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'word_ids', 'is_completed', 'words_practiced', 'created_at')
    