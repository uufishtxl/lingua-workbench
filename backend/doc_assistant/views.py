"""
API Views for Documentation Assistant

Provides SSE streaming endpoint for chat with typewriter effect.
"""
import json
from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .services import DocAssistantService


class ChatView(APIView):
    """
    POST /api/doc-assistant/chat/
    
    Chat with the documentation assistant (non-streaming).
    
    Request body:
    {
        "message": "如何创建 slice?",
        "audience": "user"  // or "developer"
    }
    
    Response:
    {
        "answer": "要创建 slice，请按以下步骤...",
        "sources": [
            {"title": "Creating a Slice", "path": "topics/slices/t_create_slice.dita"}
        ]
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        message = request.data.get('message')
        audience = request.data.get('audience', 'user')
        
        if not message:
            return Response(
                {'error': 'message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if audience not in ('user', 'developer', 'all'):
            audience = 'user'
        
        try:
            service = DocAssistantService()
            result = service.get_answer(
                question=message,
                audience=audience,
            )
            return Response(result)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChatStreamView(APIView):
    """
    POST /api/doc-assistant/chat/stream/
    
    Chat with streaming response (SSE) for typewriter effect.
    
    Request body:
    {
        "message": "如何创建 slice?",
        "audience": "user"
    }
    
    Response: Server-Sent Events stream
    - data: {"type": "token", "content": "要"}
    - data: {"type": "token", "content": "创建"}
    - ...
    - data: {"type": "sources", "sources": [...]}
    - data: {"type": "done"}
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        message = request.data.get('message')
        audience = request.data.get('audience', 'user')
        
        if not message:
            return Response(
                {'error': 'message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if audience not in ('user', 'developer', 'all'):
            audience = 'user'
        
        def event_stream():
            """Generate SSE events."""
            try:
                service = DocAssistantService()
                
                # Stream tokens
                collected_answer = []
                generator = service.stream_answer(
                    question=message,
                    audience=audience,
                )
                
                # Get search results for sources before streaming
                search_results = service.vector_store.search(
                    query=message,
                    audience=audience,
                    n_results=5,
                )
                sources = service._extract_sources(search_results)
                
                # Stream each token
                for token in generator:
                    collected_answer.append(token)
                    event_data = json.dumps({
                        "type": "token",
                        "content": token,
                    }, ensure_ascii=False)
                    yield f"data: {event_data}\n\n"
                
                # Send sources
                sources_data = json.dumps({
                    "type": "sources",
                    "sources": sources,
                }, ensure_ascii=False)
                yield f"data: {sources_data}\n\n"
                
                # Send done signal
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                
            except Exception as e:
                error_data = json.dumps({
                    "type": "error",
                    "error": str(e),
                }, ensure_ascii=False)
                yield f"data: {error_data}\n\n"
        
        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream',
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response


class IndexStatusView(APIView):
    """
    GET /api/doc-assistant/status/
    
    Get the status of the documentation index.
    
    Response:
    {
        "total_chunks": 150,
        "persist_directory": "/path/to/chroma_db"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            from .vector_store import DITAVectorStore
            store = DITAVectorStore()
            stats = store.get_stats()
            return Response(stats)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
