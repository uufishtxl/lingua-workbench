from django.contrib import admin

# Register your models here.
from .models import ScriptLine

@admin.register(ScriptLine)
class ScriptLineAdmin(admin.ModelAdmin):
    list_display = ('id', 'index', 'order', 'speaker', 'text_preview', 'line_type', 'chunk_id')
    list_filter = ('chunk__source_audio', 'line_type', 'highlight')
    search_fields = ('text', 'text_zh', 'speaker', 'action_note')
    ordering = ('chunk', 'order')
    readonly_fields = ('id', 'chunk', 'index')

    def text_preview(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
    text_preview.short_description = "Content"

