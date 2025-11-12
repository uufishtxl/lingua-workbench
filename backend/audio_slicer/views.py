from pathlib import Path

from django.core.files import File
from rest_framework import viewsets, parsers, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import SourceAudio, AudioChunk, AudioSlice, Drama
from .serializers import SourceAudioSerializer, AudioSliceSerializer, DramaSerializer, AudioChunkSerializer, AudioChunkSerializer
from .services import slice_source_to_chunks, slice_chunk_to_slice

class SourceAudioViewSet(viewsets.ModelViewSet):
    """
    API endpoint for uploading and managing source audio files.
    Triggers ffmpeg segmentation on upload.
    """
    queryset = SourceAudio.objects.all()
    serializer_class = SourceAudioSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def perform_create(self, serializer):
        # First, save the SourceAudio instance to get an ID and file path
        # We also associate the currently authenticated user.
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def episodes(self, request):
        """
        Returns a list of unique episode numbers for a given drama and season.
        """
        drama_id = request.query_params.get('drama_id')
        season = request.query_params.get('season')

        if not drama_id or not season:
            return Response({"error": "drama_id and season parameters are required."}, status=status.HTTP_400_BAD_REQUEST)

        episodes = SourceAudio.objects.filter(
            drama_id=drama_id,
            season=season
        ).values_list('episode', flat=True).distinct().order_by('episode')
        
        return Response(list(episodes))

    @action(detail=False, methods=['get'])
    def lookup(self, request):
        """
        Looks up a SourceAudio by drama, season, and episode, and returns
        its associated audio chunks if it exists.
        """
        drama_id = request.query_params.get('drama_id')
        season = request.query_params.get('season')
        episode = request.query_params.get('episode')

        if not all([drama_id, season, episode]):
            return Response(
                {"error": "drama_id, season, and episode parameters are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            source_audio = SourceAudio.objects.get(
                drama_id=drama_id,
                season=season,
                episode=episode
            )
            chunks = AudioChunk.objects.filter(source_audio=source_audio).order_by('chunk_index')
            serializer = AudioChunkSerializer(chunks, many=True)
            return Response(serializer.data)
        except SourceAudio.DoesNotExist:
            return Response(
                {"error": "SourceAudio not found."},
                status=status.HTTP_404_NOT_FOUND
            )



class AudioSliceViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing audio slices.
    """
    queryset = AudioSlice.objects.all()
    serializer_class = AudioSliceSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='create_batch')
    def create_batch(self, request):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        created_slices = []
        errors = []
        

        for item_data in serializer.validated_data:
            audio_chunk = item_data['audio_chunk']
            start_time = item_data['start_time']
            end_time = item_data['end_time']
            original_text = item_data.get('original_text', '')
            notes = item_data.get('notes', '')
            tags = item_data.get('tags', [])

            try:
                # Use the service to create the audio file and an unsaved AudioSlice instance
                audio_slice_instance = slice_chunk_to_slice(audio_chunk, start_time, end_time)
                
                # Populate other fields
                audio_slice_instance.original_text = original_text
                audio_slice_instance.notes = notes
                
                audio_slice_instance.save() # Save the instance to the database
                audio_slice_instance.tags.set(tags) # Set tags after saving
                created_slices.append(audio_slice_instance)
            except Exception as e:
                errors.append(f"Error creating slice for chunk {audio_chunk.id} from {start_time}-{end_time}: {e}")
        
        if errors:
            return Response({"message": "Some slices failed to create", "errors": errors, "created_slices": AudioSliceSerializer(created_slices, many=True).data}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(AudioSliceSerializer(created_slices, many=True).data, status=status.HTTP_201_CREATED)

class DramaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing dramas for the authenticated user.
    """
    serializer_class = DramaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all the dramas
        for the currently authenticated user.
        """
        return Drama.objects.filter(user=self.request.user)

    @action(detail=True, methods=['get'])
    def seasons(self, request, pk=None):
        """
        Returns a list of unique season numbers for a given drama.
        """
        drama = self.get_object()
        seasons = SourceAudio.objects.filter(drama=drama).values_list('season', flat=True).distinct().order_by('season')
        return Response(list(seasons))


class AudioChunkViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing dramas for the authenticated user.
    """
    serializer_class = AudioChunkSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all the dramas
        for the currently authenticated user.
        """
        return AudioChunk.objects.filter(source_audio__user=self.request.user)



