from django.db import models
from django.conf import settings

class Drama(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, unique=True, help_text="e.g., Friends, The Office")
    # 你未来还可以加海报、简介等...

    def __str__(self):
        return self.name

class AudioTag(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, unique=True, help_text="A tag for an audio slice, e.g., 'Flap T', 'H-Deletion'")

    def __str__(self):
        return self.name

class SourceAudio(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    drama = models.ForeignKey(Drama, on_delete=models.PROTECT)

    season = models.PositiveIntegerField(help_text="Season number, e.g., 10")
    episode = models.PositiveIntegerField(help_text="Episode number, e.g., 12")
    title = models.CharField(max_length=255, blank=True, help_text="Optional title for the audio source, e.g., 'The Last One'")

    file = models.FileField(upload_to='audio_slicer/originals/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('drama', 'season', 'episode')

    def __str__(self):
        return f"{self.drama.name} S{self.season:02d}E{self.episode:02d} - {self.title or 'Untitled'}"

def audio_chunk_upload_path(instance, filename):
    """
    Generates a dynamic upload path for AudioChunk files.
    e.g., media/audio_slicer/chunks/Friends_S10_E12/chunk_001.mp3
    """
    source = instance.source_audio
    drama_name = source.drama.name.replace(' ', '_')
    season_str = f"S{source.season:02d}"
    episode_str = f"E{source.episode:02d}"
    
    return f'audio_slicer/chunks/{drama_name}_{season_str}_{episode_str}/{filename}'

class AudioChunk(models.Model):
    source_audio = models.ForeignKey(SourceAudio, on_delete=models.CASCADE)
    chunk_index = models.PositiveIntegerField(help_text="Index of the chunk within the source audio (e.g., 0, 1, 2...)")
    file = models.FileField(upload_to=audio_chunk_upload_path)
    has_slices = models.BooleanField(default=False, help_text="Indicates if this chunk has any AudioSlices associated with it")
    
    class Meta:
        unique_together = ('source_audio', 'chunk_index')

    def __str__(self):
        return f"{self.source_audio.drama.name} S{self.source_audio.season:02d}E{self.source_audio.episode:02d} Chunk {self.chunk_index:03d}"


class AudioSlice(models.Model):
    """
    A slice of an audio chunk with highlights and phonetic analysis.
    
    highlights JSON format (stores raw API responses):
    [
        {
            "id": "uuid-string",
            "start": 15,           # Character position in original_text
            "end": 25,
            "focus_segment": "come along",
            "analysis": { ... },   # Raw SoundScriptResponse
            "dictionary": { ... }  # Raw DictionaryResponse
        }
    ]
    """
    audio_chunk = models.ForeignKey(AudioChunk, on_delete=models.CASCADE)
    start_time = models.FloatField(help_text="Start time of the slice in seconds")
    end_time = models.FloatField(help_text="End time of the slice in seconds")
    original_text = models.TextField(blank=True, help_text="Full text content of the audio slice")
    highlights = models.JSONField(default=list, blank=True, help_text="Highlighted segments with phonetic analysis")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('audio_chunk', 'start_time', 'end_time')

    def __str__(self):
        return f"Slice from {self.audio_chunk} ({self.start_time:.2f}s - {self.end_time:.2f}s)"