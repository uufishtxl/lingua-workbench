
import os
import django
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sample_project.settings')
django.setup()

from audio_slicer.models import AudioSlice
from django.db.models import Q
from django.contrib.auth import get_user_model

try:
    User = get_user_model()
    # Assuming first user is the one we care about
    user = User.objects.first()
    if not user:
        print("No user found")
        sys.exit(0)
        
    print(f"Checking for user: {user.username}")

    queryset = AudioSlice.objects.filter(
        audio_chunk__source_audio__user=user,
        is_idiom=True
    ).filter(
        Q(translation__isnull=True) | Q(translation__exact='')
    )

    count = queryset.count()
    print(f"Total missing translations: {count}")
    
    total = AudioSlice.objects.filter(audio_chunk__source_audio__user=user).count()
    print(f"Total audio slices for user: {total}")

except Exception as e:
    print(f"Error: {e}")
