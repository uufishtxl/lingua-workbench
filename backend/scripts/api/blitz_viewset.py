from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..models import ScriptLine
from ..serializers import BlitzCardSerializer
from django.db.models import Count, Case, When, Value, CharField, F

class BlitzCardViewSet(viewsets.GenericViewSet):
    """
    ViewSet for Blitz Camp functionality.
    GET /api/scripts/blitz-cards/ - Get cards with filters (random/shuffle)
    GET /api/scripts/blitz-cards/stats/ - Get character stats
    PATCH /api/scripts/blitz-cards/{id}/update_status/ - Update highlight status
    """
    permission_classes = [IsAuthenticated]
    serializer_class = BlitzCardSerializer

    # Shared definition for consistent "Misc" handling
    MAIN_CAST = ['Ross', 'Rachel', 'Joe', 'Joey', 'Phoebe', 'Monica', 'Chandler']

    def get_queryset(self):
        # Base queryset: Return all script lines for the user's active source audio
        return ScriptLine.objects.filter(
            chunk__source_audio__user=self.request.user
        ).select_related('slice', 'slice__audio_chunk', 'chunk')

    def list(self, request):
        """
        Get filtered list of cards.
        Params:
        - mode: 'shuffle' | 'normal'
        - status: 'hard' | 'review' | 'all'
        - character: 'All' | 'Chandler' ...
        - page/limit: handled by pagination
        """
        queryset = self.get_queryset()

        # 1. Filter by Status
        status_filter = request.query_params.get('status', 'all')
        if status_filter == 'hard':
            queryset = queryset.filter(highlight='red')
        elif status_filter == 'review':
            queryset = queryset.filter(highlight='yellow')
        elif status_filter == 'learning':
            queryset = queryset.filter(highlight__in=['red', 'yellow'])
        elif status_filter == 'all':
            pass # No filter

        print(f'status_filter: {status_filter}')

        # 2. Filter by Character
        print(f'character: {request.query_params.get("character", "All")}')
        character = request.query_params.get('character', 'All')
        if character and character != 'All':
            if character == 'Misc':
                # Exclude main characters
                queryset = queryset.exclude(speaker__in=self.MAIN_CAST)
            else:
                queryset = queryset.filter(speaker=character)

        # 3. Mode Logic
        mode = request.query_params.get('mode', 'normal')
        
        if mode == 'shuffle':
            queryset = queryset.order_by('?')
        else:
            queryset = queryset.order_by('id')

        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Return stats for Avatar Dock.
        Only counts lines marked 'red' (Hard) or 'yellow' (Review).
        Groups by main 6 Friends characters, others as 'Misc'.
        [ { "speaker": "Joey", "count": 12 }, ... ]
        """
        
        # 1. Base Queryset (Filter by highlight status)
        queryset = self.get_queryset().filter(highlight__in=['red', 'yellow'])
        
        # 2. Annotate Group
        # If speaker is in main_cast, keep it. Else, 'Misc'.
        queryset = queryset.annotate(
            group_speaker=Case(
                When(speaker__in=self.MAIN_CAST, then=F('speaker')), # 使用 F 表达式引用字段
                default=Value('Misc'),
                output_field=CharField(),
            )
        )
        
        # 4. Aggregate
        data = queryset.values('group_speaker').annotate(count=Count('id')).order_by('-count')
        
        # 5. Format Response
        results = [
            {
                "speaker": item['group_speaker'],
                "count": item['count']
            }
            for item in data
        ]
        
        return Response(results)

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """
        PATCH /api/scripts/blitz-cards/{id}/update_status/
        Body: { "status": "red" | "yellow" | "none" }
        """
        card = self.get_object()
        new_status = request.data.get('status')
        
        if new_status in ['red', 'yellow', 'none']:
            card.highlight = new_status
            card.save()
            return Response({'status': 'success', 'highlight': card.highlight})
            
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
