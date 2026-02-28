from django.contrib import admin
from .models import Article, Paragraph, Annotation

class ParagraphInline(admin.TabularInline):
    model = Paragraph
    extra = 0
    fields = ['index', 'content']
    readonly_fields = ['index', 'content']
    can_delete = False

class AnnotationInline(admin.TabularInline):
    model = Annotation
    extra = 0
    fields = ['paragraph', 'annotation_type', 'selected_text', 'user_note', 'created_at']
    readonly_fields = ['created_at']

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'site_name', 'status', 'created_at')
    list_filter = ('status', 'site_name')
    search_fields = ('title', 'url', 'author')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ParagraphInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'url', 'title', 'author', 'site_name', 'status')
        }),
        ('Content', {
            'fields': ('raw_text', 'raw_html'),
            'classes': ('collapse',)
        }),
        ('AI Context', {
            'fields': ('meta_context',),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Paragraph)
class ParagraphAdmin(admin.ModelAdmin):
    list_display = ('article', 'index', 'content_snippet')
    list_filter = ('article',)
    search_fields = ('content',)
    inlines = [AnnotationInline]

    def content_snippet(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_snippet.short_description = 'Content'

@admin.register(Annotation)
class AnnotationAdmin(admin.ModelAdmin):
    list_display = ('annotation_type', 'selected_text', 'paragraph', 'user_note', 'created_at')
    list_filter = ('annotation_type',)
    search_fields = ('selected_text', 'user_note')
    readonly_fields = ('created_at', 'updated_at')
