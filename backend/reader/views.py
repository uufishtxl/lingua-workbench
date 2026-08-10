import logging
from django.utils import timezone
from django.db import models
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from bs4 import BeautifulSoup
from .serializers import (ArticleListSerializer, ArticleDetailSerializer, ArticleCreateSerializer, 
                          ParagraphSerializer, AnnotationSerializer, BookListSerializer, BookDetailSerializer, 
                          BookCreateSerializer, ChapterListSerializer, ChapterDetailSerializer, ReadPositionSerializer)
from .models import Article, Paragraph, Annotation, Book, Chapter
from .tasks import process_article_meta_task, process_book_task
from .ai_services import assist_annotation
from .schemas import AnnotationContext

logger = logging.getLogger(__name__)


class ArticleViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Article.objects.filter(user=self.request.user).order_by('-created_at')
        # Support filtering by type
        content_type = self.request.query_params.get('type', None)
        if content_type == 'book':
            # Return empty queryset for articles when filtering for books
            return queryset.none()
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return ArticleListSerializer
        if self.action == 'create':
            return ArticleCreateSerializer
        return ArticleDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 1. Create Article
        article = serializer.save(user=self.request.user, status=Article.Status.PROCESSING)
        
        # 2. Chunk text into paragraphs
        raw_html = article.raw_html or ""
        soup = BeautifulSoup(raw_html, 'html.parser')
        
        # Extract meaningful blocks: p, li, h1-h6
        blocks = soup.find_all(['p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        import re
        text_chunks = []
        for block in blocks:
            text = block.get_text(separator=' ', strip=True)
            text = re.sub(r'\s+', ' ', text)
            if text:
                text_chunks.append(text)
        
        # Fallback to brute force splitting if HTML parsing yielded nothing over 10 chars
        if not text_chunks:
             raw_text = article.raw_text or ""
             text_chunks = [p.strip() for p in raw_text.split('\n') if p.strip()]
             
        paragraphs = []
        for index, content in enumerate(text_chunks):
            paragraphs.append(Paragraph(article=article, index=index, content=content))
            
        if paragraphs:
            Paragraph.objects.bulk_create(paragraphs)

        # 4. Trigger async task to process article meta context
        process_article_meta_task(article.id)
        
        # Return detailed representation
        headers = self.get_success_headers(serializer.data)
        detail_serializer = ArticleDetailSerializer(article)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class BookViewSet(viewsets.ModelViewSet):
    """ViewSet for managing books (PDF imports)."""
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Book.objects.filter(user=self.request.user).order_by('-created_at')
        # Support filtering by type
        content_type = self.request.query_params.get('type', None)
        if content_type == 'article':
            # Return empty queryset for books when filtering for articles
            return queryset.none()
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return BookListSerializer
        if self.action == 'create':
            return BookCreateSerializer
        return BookDetailSerializer

    def create(self, request, *args, **kwargs):
        """Upload a PDF file and create a book record."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create Book with processing status
        book = serializer.save(user=self.request.user, status=Book.Status.PROCESSING)
        
        # Trigger async task to process PDF
        process_book_task(book.id)
        
        # Return detail representation
        headers = self.get_success_headers(serializer.data)
        detail_serializer = BookDetailSerializer(book)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['put'], url_path='update-read-position')
    def update_read_position(self, request, pk=None):
        """Update the user's reading position in a book."""
        book = self.get_object()
        serializer = ReadPositionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        chapter_id = serializer.validated_data['chapter_id']
        paragraph_index = serializer.validated_data['paragraph_index']
        
        try:
            chapter = Chapter.objects.get(id=chapter_id, book=book)
        except Chapter.DoesNotExist:
            return Response({"error": "Chapter not found"}, status=status.HTTP_404_NOT_FOUND)
        
        book.last_read_chapter = chapter
        book.last_read_paragraph_index = paragraph_index
        book.last_read_at = timezone.now()
        book.save(update_fields=['last_read_chapter', 'last_read_paragraph_index', 'last_read_at'])
        
        return Response({"message": "Reading position updated"})


class ChapterViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing chapters."""
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Chapter.objects.filter(book__user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return ChapterListSerializer
        return ChapterDetailSerializer


class ParagraphViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ParagraphSerializer

    def get_queryset(self):
        return Paragraph.objects.filter(
            models.Q(article__user=self.request.user) | 
            models.Q(chapter__book__user=self.request.user)
        ).distinct()


class AnnotationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AnnotationSerializer

    def get_queryset(self):
        return Annotation.objects.filter(
            models.Q(paragraph__article__user=self.request.user) | 
            models.Q(paragraph__chapter__book__user=self.request.user)
        ).distinct().order_by('-created_at')

    @action(detail=True, methods=['post'], url_path='ai_assist')
    def ai_assist(self, request, pk=None):
        """
        Trigger dynamic AI copilot based on annotation text and type.
        """
        annotation = self.get_object()
        user_note = request.data.get('user_note', annotation.user_note)
        
        # Save user note if provided
        if user_note != annotation.user_note:
            annotation.user_note = user_note
            annotation.save()
            
        paragraph = annotation.paragraph
        # Determine the parent article (either directly or via chapter's book)
        article = paragraph.article
        if not article and paragraph.chapter:
            # For book paragraphs, we use a simplified meta_context
            domain = 'General'
        elif article and article.status == 'processing':
            return Response({"message": "AI is still analyzing the global context. Please try again soon."}, status=status.HTTP_202_ACCEPTED)
        else:
            domain = article.meta_context.get('domain', 'General') if article and article.meta_context else 'General'

        ai_res = assist_annotation(AnnotationContext(
            domain=domain,
            paragraph=paragraph.content,
            selected_text=annotation.selected_text,
            annotation_type=annotation.annotation_type,
            user_note=user_note or ""
        ))
        annotation.ai_response = ai_res
        annotation.save()
        
        serializer = self.get_serializer(annotation)
        return Response(serializer.data)


class TtsGenerateView(APIView):
    """
    POST /api/v1/tts/generate/
    Generate TTS audio for selected text using Gemini 2.5 Flash Preview TTS.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        text = request.data.get('text', '').strip()
        paragraph_id = request.data.get('paragraph_id')

        if not text:
            return Response(
                {"error": "Text is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Import the TTS function from english_corner
            from english_corner.ai_services import generate_tts_audio
            
            # Generate a unique ID for this TTS request
            import time
            request_id = int(time.time() * 1000)
            
            # Use a generic conversation_id of 0 for reader TTS
            audio_url = generate_tts_audio(text, conversation_id=0, message_id=request_id)
            
            if audio_url:
                # Save audio_url to paragraph if paragraph_id is provided
                if paragraph_id:
                    try:
                        from .models import Paragraph
                        paragraph = Paragraph.objects.get(id=paragraph_id)
                        paragraph.audio_url = audio_url
                        paragraph.save(update_fields=['audio_url'])
                    except Paragraph.DoesNotExist:
                        pass  # Paragraph not found, just return the URL
                
                return Response({"audio_url": audio_url})
            else:
                return Response(
                    {"error": "Failed to generate audio"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            logger.exception(f"TTS generation failed: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
