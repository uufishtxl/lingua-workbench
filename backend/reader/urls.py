from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ArticleViewSet, ParagraphViewSet, AnnotationViewSet

router = DefaultRouter()
router.register(r'articles', ArticleViewSet, basename='article')
router.register(r'paragraphs', ParagraphViewSet, basename='paragraph')
router.register(r'annotations', AnnotationViewSet, basename='annotation')


app_name = 'reader'

urlpatterns = [
    path('', include(router.urls)),
]
