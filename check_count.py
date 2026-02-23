
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from audio_slicer.models import AudioSlice
from django.db.models import Q
from django.contrib.auth import get_user_model

User = get_user_model()
try:
    user = User.objects.first()
    if not user:
        print("No user found")
        exit()
        
    print(f"Checking for user: {user.username}")

    queryset = AudioSlice.objects.filter(
        audio_chunk__source_audio__user=user,
        is_idiom=True
    ).filter(
        Q(translation__isnull=True) | Q(translation__exact='')
    )

    count = queryset.count()
    print(f"Total missing translations: {count}")
    
    # Also check total slices
    total = AudioSlice.objects.count()
    print(f"Total audio slices in DB: {total}")

except Exception as e:
    print(f"Error: {e}")
