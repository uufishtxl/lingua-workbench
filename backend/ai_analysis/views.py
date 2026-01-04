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
