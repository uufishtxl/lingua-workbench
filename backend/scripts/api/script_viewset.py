from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..models import ScriptLine, ScriptTask
from ..serializers import IngestRequestSerializer
from ..parser import parse_fanfr_script
from audio_slicer.models import AudioChunk, SourceAudio
from ai_analysis.services import batch_translate_idioms
from django.db.models import Q

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
