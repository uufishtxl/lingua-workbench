from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ScenarioViewSet, ConversationViewSet,
    MessageListCreateView, MessageDetailView,
    FlashcardGenerateView, ReviewTodayView, ReviewSubmitView,
    ExtractVocabView, KnowledgeGraphView,
)

router = DefaultRouter()
router.register(r'scenarios', ScenarioViewSet, basename='scenario')
router.register(r'conversations', ConversationViewSet, basename='conversation')

urlpatterns = [
    path('', include(router.urls)),

    # Messages (nested under conversations)
    path(
        'conversations/<int:conv_id>/messages/',
        MessageListCreateView.as_view(),
        name='message-list-create',
    ),
    path(
        'conversations/<int:conv_id>/messages/<int:msg_id>/',
        MessageDetailView.as_view(),
        name='message-detail',
    ),

    # Flashcard generation
    path('flashcards/generate/', FlashcardGenerateView.as_view(), name='flashcard-generate'),

    # Review
    path('review/today/', ReviewTodayView.as_view(), name='review-today'),
    path('flashcards/<int:pk>/review/', ReviewSubmitView.as_view(), name='review-submit'),

    # Vocab extraction + Knowledge graph
    path('extract/', ExtractVocabView.as_view(), name='extract-vocab'),
    path('relationship-graph/', KnowledgeGraphView.as_view(), name='knowledge-graph'),
]
