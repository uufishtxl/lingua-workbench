"""
API Views for AI analysis.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .services import analyze_sound_script


class SoundScriptAnalysisView(APIView):
    """
    POST /api/ai/sound-script/
    
    Analyze a text segment and return phonetic analysis (Sound Script).
    
    Request body:
    {
        "full_context": "You've got to live with it.",
        "focus_segment": "You've got to",
        "speed_profile": "native_fast"  // optional, defaults to "native_fast"
    }
    
    Response:
    {
        "card_type": "visual_sound_script",
        "speed_profile": "native_fast",
        "full_context": "You've got to live with it.",
        "focus_segment": "You've got to",
        "phonetic_tags": ["Reduction", "Linking"],
        "script_segments": [
            {
                "original": "You've",
                "sound_display": "Yuh",
                "ipa": "/jə/",
                "type": "Reduction",
                "is_stressed": false,
                "note": "v音脱落"
            },
            ...
        ]
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        full_context = request.data.get('full_context')
        focus_segment = request.data.get('focus_segment')
        speed_profile = request.data.get('speed_profile', 'native_fast')
        
        # Validation
        if not full_context:
            return Response(
                {'error': 'full_context is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not focus_segment:
            return Response(
                {'error': 'focus_segment is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = analyze_sound_script(
                full_context=full_context,
                focus_segment=focus_segment,
                speed_profile=speed_profile
            )
            
            # Convert Pydantic model to dict
            return Response(result.model_dump())
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DictionaryLookupView(APIView):
    """
    POST /api/ai/dictionary/
    
    Look up a word or phrase and return dictionary entry.
    
    Request body:
    {
        "full_context": "You've got to live with it.",
        "word_or_phrase": "got to"
    }
    
    Response:
    {
        "card_type": "dictionary",
        "word_or_phrase": "got to",
        "part_of_speech": "phrase",
        "definition_en": "have to; must",
        "definition_cn": "必须；不得不",
        "examples": [
            {
                "english": "I've got to go now.",
                "chinese": "我现在必须走了。"
            }
        ],
        "usage_note": "常用于口语，书面语用 have to"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        from .services import lookup_dictionary
        
        full_context = request.data.get('full_context')
        word_or_phrase = request.data.get('word_or_phrase')
        
        # Validation
        if not full_context:
            return Response(
                {'error': 'full_context is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not word_or_phrase:
            return Response(
                {'error': 'word_or_phrase is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = lookup_dictionary(
                full_context=full_context,
                word_or_phrase=word_or_phrase
            )
            
            # Convert Pydantic model to dict
            return Response(result.model_dump())
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RefreshExampleView(APIView):
    """
    POST /api/ai/refresh-example/
    
    Generate a new example sentence for a word/phrase.
    
    Request body:
    {
        "word_or_phrase": "got to"
    }
    
    Response:
    {
        "word_or_phrase": "got to",
        "example": {
            "english": "You've got to try this cake.",
            "chinese": "你一定要尝尝这个蛋糕。"
        }
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        from .services import refresh_example
        
        word_or_phrase = request.data.get('word_or_phrase')
        definition = request.data.get('definition', '')
        original_context = request.data.get('original_context', '')
        
        # Validation
        if not word_or_phrase:
            return Response(
                {'error': 'word_or_phrase is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = refresh_example(
                word_or_phrase=word_or_phrase,
                definition=definition,
                original_context=original_context
            )
            
            # Convert Pydantic model to dict
            return Response(result.model_dump())
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
