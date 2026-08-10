from django.contrib import admin

from .models import CorpusTask, Textbook, TtsText


@admin.register(Textbook)
class TextbookAdmin(admin.ModelAdmin):
    list_display = ['name', 'grade', 'semester', 'pdf_file', 'parsed_at', 'created_at']
    search_fields = ['name', 'grade']


@admin.register(CorpusTask)
class CorpusTaskAdmin(admin.ModelAdmin):
    list_display = ['name', 'textbook', 'unit', 'status', 'stage', 'extract_status', 'created_at']
    list_filter = ['status', 'stage', 'extract_status']


@admin.register(TtsText)
class TtsTextAdmin(admin.ModelAdmin):
    list_display = ['task', 'created_at']
