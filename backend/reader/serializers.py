from rest_framework import serializers
from .models import Article, Paragraph, Annotation

class AnnotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Annotation
        fields = ['id', 'paragraph', 'selected_text', 'user_note', 'annotation_type', 'ai_response', 'created_at', 'updated_at']
        read_only_fields = ['ai_response', 'created_at', 'updated_at']

class ParagraphSerializer(serializers.ModelSerializer):
    annotations = AnnotationSerializer(many=True, read_only=True)
    
    class Meta:
        model = Paragraph
        fields = ['id', 'article', 'index', 'content', 'translation', 'annotations']

class ArticleListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['id', 'url', 'title', 'author', 'site_name', 'status', 'created_at', 'updated_at']

class ArticleDetailSerializer(serializers.ModelSerializer):
    paragraphs = ParagraphSerializer(many=True, read_only=True)
    
    class Meta:
        model = Article
        fields = ['id', 'url', 'title', 'author', 'site_name', 'raw_text', 'raw_html', 'status', 'meta_context', 'paragraphs', 'created_at', 'updated_at']
        read_only_fields = ['status', 'meta_context', 'created_at', 'updated_at']

class ArticleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['url', 'title', 'author', 'site_name', 'raw_text', 'raw_html']


