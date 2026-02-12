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
    After slicing, schedule a background task to ingest and translate the script.
    """
    if created:
        print(f"Triggering slice logic for SourceAudio: {instance.id}")
        slice_source_to_chunks(instance)

        # Schedule background script ingest + translate task
        from scripts.models import ScriptTask
        from scripts.tasks import ingest_and_translate_script

        script_task = ScriptTask.objects.create(
            source_audio=instance,
            status='pending',
            message=f'Queued for S{instance.season:02d}E{instance.episode:02d}',
        )
        ingest_and_translate_script(script_task.id)
        print(f"Scheduled script ingest+translate task #{script_task.id} for SourceAudio: {instance.id}")
