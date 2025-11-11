from django.apps import AppConfig


class AudioSlicerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audio_slicer'

    def ready(self):
        import audio_slicer.signals  # noqa

