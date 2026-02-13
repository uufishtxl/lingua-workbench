from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.shortcuts import get_object_or_404
from ..models import ScriptLine
from ..serializers import ScriptLineListSerializer, SplitRequestSerializer
from audio_slicer.models import AudioChunk, AudioSlice
import os

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

    def search_slices(self, request, pk=None):
        """
        POST /api/scripts/lines/{id}/search-slices/
        Find the best matching AudioSlice for a ScriptLine using
        embedding similarity (cosine). Searches within the same chunk.
        """
        import numpy as np
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        from django.conf import settings

        line = get_object_or_404(ScriptLine, pk=pk)

        # Check ownership
        if line.chunk.source_audio.user != request.user:
            return Response(
                {'error': 'Unauthorized'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get all AudioSlices in the same chunk
        slices = AudioSlice.objects.filter(
            audio_chunk=line.chunk
        ).order_by('start_time')

        if not slices.exists():
            return Response({
                'results': [],
                'message': 'No audio slices found in this chunk.',
            })

        # Prepare texts
        query_text = line.text
        candidate_texts = [s.original_text for s in slices]

        # Filter out empty texts
        valid_pairs = [
            (s, t) for s, t in zip(slices, candidate_texts)
            if t and t.strip()
        ]
        if not valid_pairs:
            return Response({
                'results': [],
                'message': 'No audio slices with text found in this chunk.',
            })

        valid_slices, valid_texts = zip(*valid_pairs)

        # Compute embeddings
        api_key = os.getenv('GOOGLE_API_KEY') or ''
        embeddings_model = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=api_key,
        )

        # Batch: embed query + all candidates in one call
        all_texts = [query_text] + list(valid_texts)
        all_embeddings = embeddings_model.embed_documents(all_texts)

        query_vec = np.array(all_embeddings[0])
        candidate_vecs = np.array(all_embeddings[1:])

        # Cosine similarity
        dot_products = candidate_vecs @ query_vec
        query_norm = np.linalg.norm(query_vec)
        candidate_norms = np.linalg.norm(candidate_vecs, axis=1)
        similarities = dot_products / (query_norm * candidate_norms + 1e-10)

        # Rank and pick top 3
        top_indices = np.argsort(similarities)[::-1][:3]

        results = []
        for idx in top_indices:
            s = valid_slices[idx]
            results.append({
                'slice_id': s.id,
                'original_text': s.original_text,
                'translation': s.translation or '',
                'start_time': s.start_time,
                'end_time': s.end_time,
                'similarity': round(float(similarities[idx]), 4),
            })

        return Response({
            'query_text': query_text,
            'results': results,
        })

    def bind_slice(self, request, pk=None):
        """
        POST /api/scripts/lines/{id}/bind-slice/
        Body: { "slice_id": 42 }
        Bind a ScriptLine to a specific AudioSlice.
        """
        line = get_object_or_404(ScriptLine, pk=pk)

        # Check ownership
        if line.chunk.source_audio.user != request.user:
            return Response(
                {'error': 'Unauthorized'},
                status=status.HTTP_403_FORBIDDEN
            )

        slice_id = request.data.get('slice_id')
        if slice_id is None:
            return Response(
                {'error': 'slice_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        audio_slice = get_object_or_404(AudioSlice, pk=slice_id)
        line.slice = audio_slice
        line.save()

        return Response({
            'line_id': line.id,
            'slice_id': audio_slice.id,
            'message': f'Line #{line.id} bound to slice #{audio_slice.id}',
        })

