import os
import sys
import django
from django.conf import settings

# Setup Django Environment
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lingua_backend.settings')
django.setup()

from scripts.models import ScriptLine
from scripts.serializers import BlitzCardSerializer

# Test Serializer Output
print("--- Testing BlitzCardSerializer ---")
try:
    # Get a Sample ScriptLine
    sl = ScriptLine.objects.filter(chunk__source_audio__isnull=False).first()
    if not sl:
        print("No ScriptLine found with Chunk and SourceAudio!")
        exit(1)

    print(f"Testing with ScriptLine ID: {sl.id}")
    serializer = BlitzCardSerializer(sl)
    data = serializer.data
    
    print("\nSerialized Data:")
    import json
    print(json.dumps(data, indent=2, ensure_ascii=False))

    # Validate Structure
    assert 'speaker' in data, "Missing 'speaker' field"
    assert isinstance(data['speaker'], dict), "'speaker' should be a dict"
    assert 'avatar_url' in data['speaker'], "Missing 'speaker.avatar_url'"
    assert 'theme_color' in data['speaker'], "Missing 'speaker.theme_color'"
    
    assert 'content' in data, "Missing 'content' field"
    assert isinstance(data['content'], dict), "'content' should be a dict"
    assert 'text' in data['content'], "Missing 'content.text'"
    assert 'audio_url' in data['content'], "Missing 'content.audio_url'"
    
    assert 'episode' in data, "Missing 'episode' field"
    assert 'order' in data, "Missing 'order' field"
    
    print("\n✅ Verification Successful: Serializer output matches expected nested structure.")

except Exception as e:
    print(f"\n❌ Verification Failed: {e}")
    import traceback
    traceback.print_exc()
