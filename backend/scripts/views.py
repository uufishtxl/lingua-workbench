from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.shortcuts import get_object_or_404

from .models import ScriptLine
from .serializers import (
    ScriptLineListSerializer,
    SplitRequestSerializer,
    IngestRequestSerializer,
)
from .parser import parse_fanfr_script
from audio_slicer.models import AudioChunk, SourceAudio


class ScriptViewSet(viewsets.ViewSet):
    """
    ViewSet for script operations.
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def ingest(self, request):
        """
        Ingest a script from fanfr.com into the database.
        POST /api/scripts/ingest/
        Body: { "season": 10, "episode": 13 }
        """
        serializer = IngestRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        season = serializer.validated_data['season']
        episode = serializer.validated_data['episode']
        
        # Find the source audio by season and episode
        source_audio = SourceAudio.objects.filter(
            user=request.user,
            season=season,
            episode=episode
        ).first()
        
        if not source_audio:
            return Response(
                {'error': f'No source audio found for S{season:02d}E{episode:02d}'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get the first chunk
        first_chunk = AudioChunk.objects.filter(source_audio=source_audio).order_by('chunk_index').first()
        
        if not first_chunk:
            return Response(
                {'error': 'No audio chunks found for this source audio'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse the script
        try:
            parsed_lines = parse_fanfr_script(season, episode)
        except Exception as e:
            return Response(
                {'error': f'Failed to parse script: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not parsed_lines:
            return Response(
                {'error': 'No script lines parsed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Delete existing script lines for this chunk (if re-ingesting)
        ScriptLine.objects.filter(chunk__source_audio=source_audio).delete()
        
        # Create script lines
        script_lines = []
        for idx, line_data in enumerate(parsed_lines):
            script_lines.append(ScriptLine(
                chunk=first_chunk,
                index=idx,
                line_type=line_data['type'],
                speaker=line_data.get('speaker'),
                text=line_data['text'],
                action_note=line_data.get('action_note'),
                raw_text=line_data['raw_text'],
            ))
        
        ScriptLine.objects.bulk_create(script_lines)
        
        return Response({
            'created': len(script_lines),
            'target_chunk_id': first_chunk.id
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """
        Delete all script lines for a source audio.
        DELETE /api/scripts/clear/?season=10&episode=13
        """
        season = request.query_params.get('season')
        episode = request.query_params.get('episode')
        
        if not season or not episode:
            return Response(
                {'error': 'season and episode are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        source_audio = SourceAudio.objects.filter(
            user=request.user,
            season=int(season),
            episode=int(episode)
        ).first()
        
        if not source_audio:
            return Response(
                {'error': f'No source audio found for S{int(season):02d}E{int(episode):02d}'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        deleted_count, _ = ScriptLine.objects.filter(chunk__source_audio=source_audio).delete()
        
        return Response({
            'deleted': deleted_count,
            'source_audio_id': source_audio.id
        })

    @action(detail=False, methods=['post'])
    def translate(self, request):
        """
        Batch translate script lines for a source audio.
        POST /api/scripts/translate/
        Body: { "season": 10, "episode": 13 }
        
        Translates all script lines that don't have text_zh yet.
        """
        from ai_analysis.services import batch_translate_idioms
        
        season = request.data.get('season')
        episode = request.data.get('episode')
        
        if not season or not episode:
            return Response(
                {'error': 'season and episode are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find source audio
        source_audio = SourceAudio.objects.filter(
            user=request.user,
            season=int(season),
            episode=int(episode)
        ).first()
        
        if not source_audio:
            return Response(
                {'error': f'No source audio found for S{int(season):02d}E{int(episode):02d}'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get script lines without translation
        from django.db.models import Q
        lines_to_translate = ScriptLine.objects.filter(
            chunk__source_audio=source_audio
        ).filter(
            Q(text_zh__isnull=True) | Q(text_zh__exact='')
        ).order_by('index')
        
        if not lines_to_translate.exists():
            return Response({
                'message': 'All script lines already have translations',
                'translated_count': 0
            })
        
        # Prepare data for translation (batch by 50)
        BATCH_SIZE = 50
        total_translated = 0
        
        all_lines = list(lines_to_translate.values('id', 'text'))
        
        for i in range(0, len(all_lines), BATCH_SIZE):
            batch = all_lines[i:i + BATCH_SIZE]
            # Format for batch_translate_idioms: [{'id': 1, 'text': '...'}]
            
            try:
                translations = batch_translate_idioms(batch)
                
                # Update database
                for item in translations:
                    line_id = item.get('id')
                    translation = item.get('translation')
                    if line_id and translation:
                        ScriptLine.objects.filter(id=line_id).update(text_zh=translation)
                        total_translated += 1
                        
            except Exception as e:
                return Response({
                    'error': f'Translation failed at batch {i//BATCH_SIZE}: {str(e)}',
                    'translated_so_far': total_translated
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'message': f'Successfully translated {total_translated} lines',
            'translated_count': total_translated,
            'total_lines': len(all_lines)
        })

    @action(detail=False, methods=['get'])
    def task_status(self, request):
        """
        Get the latest script task status for a source audio.
        GET /api/scripts/task_status/?source_audio_id=123
        """
        from .models import ScriptTask

        source_audio_id = request.query_params.get('source_audio_id')
        if not source_audio_id:
            return Response(
                {'error': 'source_audio_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        task = ScriptTask.objects.filter(
            source_audio_id=source_audio_id,
            source_audio__user=request.user,
        ).first()

        if not task:
            return Response(
                {'error': 'No script task found'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            'id': task.id,
            'status': task.status,
            'message': task.message,
            'ingest_count': task.ingest_count,
            'translate_count': task.translate_count,
            'created_at': task.created_at.isoformat(),
            'updated_at': task.updated_at.isoformat(),
        })


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
        
        from .serializers import ScriptLineListSerializer
        return Response(ScriptLineListSerializer(line).data)

    def list(self, request, chunk_pk=None):
        """
        GET /api/scripts/chunk/{chunk_id}/lines/?limit=50
        Returns script lines for a chunk.
        """
        chunk = get_object_or_404(AudioChunk, pk=chunk_pk)
        limit = int(request.query_params.get('limit', 50))
        
        lines = ScriptLine.objects.filter(chunk=chunk).order_by('index')[:limit]
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


class BlitzCardViewSet(viewsets.GenericViewSet):
    """
    ViewSet for Blitz Camp functionality.
    GET /api/scripts/blitz-cards/ - Get cards with filters (random/shuffle)
    GET /api/scripts/blitz-cards/stats/ - Get character stats
    PATCH /api/scripts/blitz-cards/{id}/update_status/ - Update highlight status
    """
    permission_classes = [IsAuthenticated]
    from .serializers import BlitzCardSerializer
    serializer_class = BlitzCardSerializer

    def get_queryset(self):
        # Base queryset: Return all script lines for the user's active source audio
        # We relax the slice check so we can at least see the text even if audio isn't linked yet.
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

        # 2. Filter by Character
        character = request.query_params.get('character', 'All')
        if character and character != 'All':
            queryset = queryset.filter(speaker=character)

        # 3. Mode Logic
        mode = request.query_params.get('mode', 'normal')
        
        if mode == 'shuffle':
            # Session-based random shuffle exclusion
            # Get list of IDs already seen in this "session" (frontend reset clears this?)
            # Actually, frontend manages page=1 reset. Backend just serves random.
            # To avoid repeats, we can store seen_ids in session if we want strict non-repeat.
            
            # Simple approach: Order by random
            queryset = queryset.order_by('?')
            
            # If we want to implement session-based non-repeat:
            # seen_ids = request.session.get('blitz_seen_ids', [])
            # queryset = queryset.exclude(id__in=seen_ids)
        else:
            # Normal mode: Order by sequence (maybe by updated_at or create?)
            # Or simplified: Order by id
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
        from django.db.models import Count, Case, When, Value, CharField, F
        
        # 1. Base Queryset (Filter by highlight status)
        queryset = self.get_queryset().filter(highlight__in=['red', 'yellow'])
        
        # 2. Define Main Cast
        main_cast = ['Monica', 'Rachel', 'Phoebe', 'Chandler', 'Joey', 'Ross']
        
        # 3. Annotate Group
        # If speaker is in main_cast, keep it. Else, 'Misc'.
        queryset = queryset.annotate(
            group_speaker=Case(
                When(speaker__in=main_cast, then=F('speaker')), # 使用 F 表达式引用字段
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
