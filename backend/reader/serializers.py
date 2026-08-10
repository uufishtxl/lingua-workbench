from rest_framework import serializers
from .models import Article, Paragraph, Annotation, Book, Chapter


class AnnotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Annotation
        fields = ['id', 'paragraph', 'selected_text', 'user_note', 'annotation_type', 'ai_response', 'created_at', 'updated_at']
        read_only_fields = ['ai_response']


class ParagraphSerializer(serializers.ModelSerializer):
    annotations = AnnotationSerializer(many=True, read_only=True)
    
    class Meta:
        model = Paragraph
        fields = ['id', 'article', 'chapter', 'index', 'content', 'translation', 'annotations', 'audio_url']
        read_only_fields = ['article', 'chapter', 'index', 'content', 'translation', 'audio_url']


class BookListSerializer(serializers.ModelSerializer):
    """Serializer for book list view."""
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'original_filename', 'status', 'created_at', 'updated_at']


class BookDetailSerializer(serializers.ModelSerializer):
    """Serializer for book detail view with chapters."""
    chapters = serializers.SerializerMethodField()
    
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'original_filename', 'status', 'meta_context', 
                  'last_read_chapter', 'last_read_paragraph_index', 'last_read_at',
                  'chapters', 'created_at', 'updated_at']
        read_only_fields = ['status', 'meta_context', 'last_read_chapter', 'last_read_paragraph_index', 'last_read_at']
    
    def get_chapters(self, obj):
        chapters = obj.chapters.all().order_by('chapter_index')
        return ChapterListSerializer(chapters, many=True).data


class BookCreateSerializer(serializers.ModelSerializer):
    """Serializer for book creation (file upload)."""
    class Meta:
        model = Book
        fields = ['title', 'author', 'original_filename', 'pdf_file']


class ChapterListSerializer(serializers.ModelSerializer):
    """Serializer for chapter list view."""
    class Meta:
        model = Chapter
        fields = ['id', 'title', 'chapter_index', 'start_page', 'end_page', 'status']


class ChapterDetailSerializer(serializers.ModelSerializer):
    """Serializer for chapter detail view with paragraphs."""
    paragraphs = ParagraphSerializer(many=True, read_only=True)
    
    class Meta:
        model = Chapter
        fields = ['id', 'book', 'title', 'chapter_index', 'start_page', 'end_page', 'status', 'paragraphs', 'created_at', 'updated_at']
        read_only_fields = ['status']


class ReadPositionSerializer(serializers.Serializer):
    """Serializer for updating reading position."""
    chapter_id = serializers.IntegerField()
    paragraph_index = serializers.IntegerField(default=0)


class ArticleListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['id', 'title', 'author', 'status', 'created_at', 'updated_at']


class ArticleDetailSerializer(serializers.ModelSerializer):
    paragraphs = ParagraphSerializer(many=True, read_only=True)
    
    class Meta:
        model = Article
        fields = ['id', 'url', 'title', 'author', 'site_name', 'raw_text', 'raw_html', 'status', 'meta_context', 'paragraphs', 'created_at', 'updated_at']
        read_only_fields = ['status', 'meta_context']


class ArticleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['url', 'title', 'author', 'site_name', 'raw_text', 'raw_html']
