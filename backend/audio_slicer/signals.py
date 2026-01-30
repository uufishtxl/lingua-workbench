from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import AudioSlice, ReviewCard, SourceAudio
from .services import slice_source_to_chunks

@receiver(post_save, sender=AudioSlice)
def create_review_card_if_idiom(sender, instance, created, **kwargs):
    """
    Automatically create a ReviewCard if an AudioSlice is marked as an idiom (is_idiom=True).
    The card is scheduled for immediate review (next_review_date = today).
    """
    if instance.is_idiom:
        # Check if card already exists
        if not hasattr(instance, 'review_card'):
            # Determine review type based on translation availability
            # (Though logic can be dynamic in frontend, we set a reasonable default here)
            review_type = 'translation' if instance.translation else 'listening'
            
            ReviewCard.objects.create(
                audio_slice=instance,
                user=instance.audio_chunk.source_audio.user, # Inherit owner from parent Audio -> Source
                next_review_date=timezone.now().date(),      # Due immediately
                review_type=review_type
            )

@receiver(post_save, sender=SourceAudio)
def trigger_audio_slicing(sender, instance, created, **kwargs):
    """
    Trigger the slicing process when a SourceAudio is created (uploaded).
    """
    if created:
        print(f"Triggering slice logic for SourceAudio: {instance.id}")
        # Note: This is a synchronous call. For large files, this should be moved to a background task (e.g. Huey).
        # But for now, user requested simplicity or it fits the current architecture.
        slice_source_to_chunks(instance)
