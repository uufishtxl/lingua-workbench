from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ScriptViewSet, ScriptLineViewSet, BlitzCardViewSet

router = DefaultRouter()
router.register(r'blitz-cards', BlitzCardViewSet, basename='blitz-cards')
router.register(r'', ScriptViewSet, basename='scripts')

urlpatterns = [
    path('', include(router.urls)),
    # Individual line operations
    path('lines/<int:pk>/', ScriptLineViewSet.as_view({
        'patch': 'partial_update',
    }), name='script-line-detail'),
    # Nested routes for chunk-specific operations
    path('chunk/<int:chunk_pk>/lines/', ScriptLineViewSet.as_view({
        'get': 'list',
    }), name='script-lines-list'),
    path('chunk/<int:chunk_pk>/split/', ScriptLineViewSet.as_view({
        'post': 'split',
    }), name='script-split'),
    path('chunk/<int:chunk_pk>/undo-split/', ScriptLineViewSet.as_view({
        'post': 'undo_split',
    }), name='script-undo-split'),
]

