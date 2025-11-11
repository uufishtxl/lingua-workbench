from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SourceAudio
from .services import slice_source_to_chunks

@receiver(post_save, sender=SourceAudio)
def source_audio_post_save(sender, instance, created, **kwargs):
    """
    Handles post-save operations for SourceAudio instances.
    If a new SourceAudio is created, it triggers the slicing into chunks.
    """
    if created:
        try:
            slice_source_to_chunks(instance)
        except Exception as e:
            # Log the error and potentially handle it (e.g., mark SourceAudio as failed)
            print(f"Error slicing SourceAudio {instance.id}: {e}")
            # You might want to add a field to SourceAudio to mark processing status
            # instance.processing_status = 'FAILED'
            # instance.save()
