from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.shortcuts import get_object_or_404
from ..models import ScriptLine
from ..serializers import ScriptLineListSerializer, SplitRequestSerializer
from audio_slicer.models import AudioChunk

class ScriptLineViewSet(viewsets.ViewSet):
    """
    ViewSet for script line operations within a chunk.
    """
    permission_classes = [IsAuthenticated]

    def partial_update(self, request, pk=None):
        """
        PATCH /api/scripts/lines/{id}/
        Update a single script line (highlight, etc.)
        """
        line = get_object_or_404(ScriptLine, pk=pk)
        
        # Check ownership
        if line.chunk.source_audio.user != request.user:
            return Response(
                {'error': 'Unauthorized'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update allowed fields
        if 'highlight' in request.data:
            line.highlight = request.data['highlight']
        
        line.save()
        
        return Response(ScriptLineListSerializer(line).data)

    def list(self, request, chunk_pk=None):
        """
        GET /api/scripts/chunk/{chunk_id}/lines/?limit=50
        Returns script lines for a chunk.
        """
        chunk = get_object_or_404(AudioChunk, pk=chunk_pk)
        limit = int(request.query_params.get('limit', 50))
        
        lines = ScriptLine.objects.filter(chunk=chunk).order_by('order')[:limit]
        serializer = ScriptLineListSerializer(lines, many=True)
        
        total_count = ScriptLine.objects.filter(chunk=chunk).count()
        
        return Response({
            'results': serializer.data,
            'count': total_count,
            'limit': limit,
        })

    @action(detail=False, methods=['post'])
    def split(self, request, chunk_pk=None):
        """
        POST /api/scripts/chunk/{chunk_id}/split/
        Body: { "start_index": 21, "next_chunk_id": 14 }
        Move lines from start_index onwards to next_chunk.
        """
        serializer = SplitRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        start_index = serializer.validated_data['start_index']
        next_chunk_id = serializer.validated_data['next_chunk_id']
        
        current_chunk = get_object_or_404(AudioChunk, pk=chunk_pk)
        next_chunk = get_object_or_404(AudioChunk, pk=next_chunk_id)
        
        with transaction.atomic():
            moved_count = ScriptLine.objects.filter(
                chunk=current_chunk,
                index__gte=start_index
            ).update(chunk=next_chunk)
        
        return Response({
            'moved_count': moved_count,
            'from_chunk_id': current_chunk.id,
            'to_chunk_id': next_chunk.id,
            'start_index': start_index,
        })

    @action(detail=False, methods=['post'], url_path='undo-split')
    def undo_split(self, request, chunk_pk=None):
        """
        POST /api/scripts/chunk/{chunk_id}/undo-split/
        Body: { "from_chunk_id": 14 }
        Move all lines from from_chunk back to this chunk.
        """
        from_chunk_id = request.data.get('from_chunk_id')
        if not from_chunk_id:
            return Response(
                {'error': 'from_chunk_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        current_chunk = get_object_or_404(AudioChunk, pk=chunk_pk)
        from_chunk = get_object_or_404(AudioChunk, pk=from_chunk_id)
        
        with transaction.atomic():
            moved_count = ScriptLine.objects.filter(
                chunk=from_chunk
            ).update(chunk=current_chunk)
        
        return Response({
            'moved_count': moved_count,
            'to_chunk_id': current_chunk.id,
            'from_chunk_id': from_chunk.id,
        })
