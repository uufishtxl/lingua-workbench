from pathlib import Path

from django.core.files import File
from rest_framework import viewsets, parsers, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import SourceAudio, AudioChunk, AudioSlice, Drama
from .serializers import SourceAudioSerializer, AudioSliceSerializer, DramaSerializer, AudioChunkSerializer
from .services import slice_source_to_chunks

class SourceAudioViewSet(viewsets.ModelViewSet):
    """
    API endpoint for uploading and managing source audio files.
    Triggers ffmpeg segmentation on upload.
    """
    # queryset = SourceAudio.objects.all() # Removed static queryset
    serializer_class = SourceAudioSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def get_queryset(self):
        """
        This view should return a list of all the SourceAudio objects
        for the currently authenticated user.
        """
        return SourceAudio.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        drama_value = request.data.get('drama')

        # Handle case where drama is a string name instead of an ID
        if drama_value and isinstance(drama_value, str) and not drama_value.isdigit():
            drama_name = drama_value
            
            # Since Drama.name is unique, we can't have two users with the same drama name.
            # We get or create, but ensure it's associated with the current user.
            drama, created = Drama.objects.get_or_create(
                name=drama_name,
                defaults={'user': request.user}
            )

            # If the drama was not created, it means it already existed.
            # We must verify that it belongs to the current user.
            if not created and drama.user != request.user:
                return Response(
                    {"error": f"A drama with the name '{drama_name}' already exists and is owned by another user."},
                    status=status.HTTP_409_CONFLICT
                )

            # Mutate the request data to replace the drama name with the drama ID
            mutable_data = {key: value for key, value in request.data.items()}
            mutable_data['drama'] = drama.id
            
            # Proceed with the serializer and standard creation flow
            serializer = self.get_serializer(data=mutable_data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        # If drama is an ID or not provided, proceed with default behavior
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        if not serializer.validated_data.get('title'):
            season = serializer.validated_data.get('season')
            episode = serializer.validated_data.get('episode')
            if season is not None and episode is not None:
                serializer.validated_data['title'] = f"S{season:02d}E{episode:02d}"
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
            user=request.user,
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
    # queryset = AudioSlice.objects.all() # Removed static queryset
    serializer_class = AudioSliceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return AudioSlice objects for the authenticated user.
        Optional filter by audio_chunk query param.
        """
        queryset = AudioSlice.objects.filter(audio_chunk__source_audio__user=self.request.user)
        
        # Filter by audio_chunk if provided
        audio_chunk_id = self.request.query_params.get('audio_chunk')
        if audio_chunk_id:
            queryset = queryset.filter(audio_chunk_id=audio_chunk_id)
        
        return queryset.order_by('start_time')

    @action(detail=False, methods=['post'], url_path='create_batch')
    def create_batch(self, request):
        """
        Create multiple AudioSlice records in a batch.
        No longer cuts audio files - just stores metadata with highlights.
        """
        serializer = self.get_serializer(data=request.data, many=True)
        if not serializer.is_valid():
            print("Serializer validation errors:", serializer.errors)
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        created_slices = []
        errors = []

        for item_data in serializer.validated_data:
            audio_chunk = item_data['audio_chunk']
            
            # Verify the user owns this chunk
            if audio_chunk.source_audio.user != request.user:
                errors.append(f"Unauthorized: chunk {audio_chunk.id} does not belong to current user")
                continue

            try:
                slice_id = item_data.get('id')
                defaults = {
                    'audio_chunk': audio_chunk,
                    'start_time': item_data['start_time'],
                    'end_time': item_data['end_time'],
                    'original_text': item_data.get('original_text', ''),
                    'highlights': item_data.get('highlights', []),
                    'is_favorite': item_data.get('is_favorite', False)
                }
                
                if slice_id:
                    # Update by ID if provided (allows time changes)
                    slice_obj, created = AudioSlice.objects.update_or_create(
                        id=slice_id,
                        defaults=defaults
                    )
                else:
                    # Fallback: create new or update by time-based lookup
                    slice_obj, created = AudioSlice.objects.update_or_create(
                        audio_chunk=audio_chunk,
                        start_time=item_data['start_time'],
                        end_time=item_data['end_time'],
                        defaults={
                            'original_text': item_data.get('original_text', ''),
                            'highlights': item_data.get('highlights', []),
                            'is_favorite': item_data.get('is_favorite', False)
                        }
                    )
                created_slices.append(slice_obj)
                
                # Mark the chunk as having slices
                if not audio_chunk.has_slices:
                    audio_chunk.has_slices = True
                    audio_chunk.save()
                    
            except Exception as e:
                errors.append(f"Error creating slice for chunk {audio_chunk.id}: {e}")
        
        if errors:
            return Response({
                "message": "Some slices failed to create", 
                "errors": errors, 
                "created_slices": AudioSliceSerializer(created_slices, many=True).data
            }, status=status.HTTP_400_BAD_REQUEST)
        
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



