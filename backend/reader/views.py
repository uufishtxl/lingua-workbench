import logging
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from bs4 import BeautifulSoup # Moved from inside create method to top-level import as per user's edit
from .serializers import ArticleListSerializer, ArticleDetailSerializer, ArticleCreateSerializer, ParagraphSerializer, AnnotationSerializer
from .models import Article, Paragraph, Annotation
from .tasks import process_article_meta_task # Added import
from .ai_services import assist_annotation # Added import
from .schemas import AnnotationContext

logger = logging.getLogger(__name__)

class ArticleViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Article.objects.filter(user=self.request.user).order_by('-created_at')

    def get_serializer_class(self):
        if self.action in ['list']:
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
        # Readability's raw_text doesn't always have \n\n. Parsing the HTML is safer.
        
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
        process_article_meta_task(article.id) # Added task trigger
        
        # Return detailed representation
        headers = self.get_success_headers(serializer.data)
        detail_serializer = ArticleDetailSerializer(article)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ParagraphViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ParagraphSerializer

    def get_queryset(self):
        return Paragraph.objects.filter(article__user=self.request.user)


class AnnotationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AnnotationSerializer

    def get_queryset(self):
        return Annotation.objects.filter(paragraph__article__user=self.request.user).order_by('-created_at')

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
            
        article = annotation.paragraph.article
        if article.status == 'processing':
            # Handle Async Gap gracefully
            return Response({"message": "AI is still analyzing the global context. Please try again soon."}, status=status.HTTP_202_ACCEPTED)

        # Call actual LLM logic from ai_services
        try:
            domain = article.meta_context.get('domain', 'General') if article.meta_context else 'General'
            ai_res = assist_annotation(AnnotationContext(
                domain=domain,
                paragraph=annotation.paragraph.content,
                selected_text=annotation.selected_text,
                annotation_type=annotation.annotation_type,
                user_note=user_note or ""
            ))
            annotation.ai_response = ai_res
        except Exception as e:
            annotation.ai_response = {"content": f"Failed to reach AI: {str(e)}"}
            
        annotation.save()
        
        serializer = self.get_serializer(annotation)
        return Response(serializer.data)



