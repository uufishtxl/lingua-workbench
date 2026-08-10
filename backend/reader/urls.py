from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ArticleViewSet, BookViewSet, ChapterViewSet, ParagraphViewSet, AnnotationViewSet, TtsGenerateView

router = DefaultRouter()
router.register(r'articles', ArticleViewSet, basename='article')
router.register(r'books', BookViewSet, basename='book')
router.register(r'chapters', ChapterViewSet, basename='chapter')
router.register(r'paragraphs', ParagraphViewSet, basename='paragraph')
router.register(r'annotations', AnnotationViewSet, basename='annotation')


app_name = 'reader'

urlpatterns = [
    path('tts/generate/', TtsGenerateView.as_view(), name='tts-generate'),
    path('', include(router.urls)),
]
