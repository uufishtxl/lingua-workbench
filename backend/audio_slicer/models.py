from django.db import models
from django.conf import settings
import re

class Drama(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255, unique=True, help_text="e.g., Friends, The Office")
    
    # [NEW] Cover image for Dashboard display (Retained due to historical data)
    cover_image = models.ImageField(
        upload_to='covers/%Y/%m/',
        null=True,
        blank=True,
        help_text="剧集封面/海报"
    )

    def __str__(self):
        return self.name

class AudioTag(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, unique=True, help_text="A tag for an audio slice, e.g., 'Flap T', 'H-Deletion'")

    def __str__(self):
        return self.name

class SourceAudio(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    drama = models.ForeignKey(Drama, on_delete=models.PROTECT, related_name='audios')

    season = models.PositiveIntegerField(help_text="Season number, e.g., 10")
    episode = models.PositiveIntegerField(help_text="Episode number, e.g., 12")
    title = models.CharField(max_length=255, blank=True, default="", help_text="Optional title for the audio source, e.g., 'The Last One'")

    file = models.FileField(upload_to='audio_slicer/originals/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Cover image for this episode (for Dashboard display & plot recall)
    cover_image = models.ImageField(
        upload_to='covers/episodes/%Y/%m/',
        null=True,
        blank=True,
        help_text="Episode cover/screenshot for plot recall"
    )

    class Meta:
        ordering = ['drama', 'season', 'episode']
        constraints = [
            models.UniqueConstraint(fields=['drama', 'season', 'episode'], name='unique_episode')
        ]

    def save(self, *args, **kwargs):
        if not self.title:
            self.title = f"{self.drama.name} S{self.season} E{self.episode}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.drama.name} S{self.season:02d}E{self.episode:02d} - {self.title or 'Untitled'}"

def audio_chunk_upload_path(instance, filename):
    """
    Generates a dynamic upload path for AudioChunk files.
    e.g., media/audio_slicer/chunks/Friends_S10_E12/chunk_001.mp3
    """
    source = instance.source_audio
    # [核心改造] 正则：清洗掉除了大小写字母、数字、破折号和下划线以外的任何牛鬼蛇神！
    # [^\w\s-] 意思是匹配所有不是字母、数字、下划线、空格和减号的字符，替换为空。
    # 然后再把空格收缩为下划线
    drama_name = re.sub(r'[^\w\s-]', '', source.drama.name).strip().replace(' ', '_')
    season_str = f"S{source.season:02d}"
    episode_str = f"E{source.episode:02d}"
    
    return f'audio_slicer/chunks/{drama_name}_{season_str}_{episode_str}/{filename}'

class AudioChunk(models.Model):
    source_audio = models.ForeignKey(SourceAudio, on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.PositiveIntegerField(help_text="Index of the chunk within the source audio (e.g., 0, 1, 2...)")
    file = models.FileField(upload_to=audio_chunk_upload_path)
    has_slices = models.BooleanField(default=False, help_text="Indicates if this chunk has any AudioSlices associated with it")
    
    # [NEW] Progress tracking for Dashboard
    is_studied = models.BooleanField(default=False, db_index=True, help_text="已完成复习")
    last_studied_at = models.DateTimeField(null=True, blank=True, help_text="最后复习时间")
    
    class Meta:
        ordering = ['source_audio', 'chunk_index']  # Ensure consistent ordering
        constraints = [
            models.UniqueConstraint(fields=['source_audio', 'chunk_index'], name='unique_chunk_within_audio')
        ]

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
    audio_chunk = models.ForeignKey(AudioChunk, on_delete=models.CASCADE, related_name='slices')
    start_time = models.FloatField(help_text="Start time of the slice in seconds")
    end_time = models.FloatField(help_text="End time of the slice in seconds")
    original_text = models.TextField(blank=True, help_text="Full text content of the audio slice")
    highlights = models.JSONField(default=list, blank=True, help_text="Highlighted segments with phonetic analysis")

    translation = models.TextField(blank=True, null=True, help_text="Chinese translation for SRS review")
    
    is_pronunciation_hard = models.BooleanField(default=False, help_text="Mark slice as hard for pronunciation")
    is_idiom = models.BooleanField(default=False, help_text="Mark slice as containing idioms (Auto-triggers ReviewCard creation)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['audio_chunk', 'start_time', 'end_time'], name='unique_slice_times')
        ]

    def __str__(self):
        return f"Slice from {self.audio_chunk} ({self.start_time:.2f}s - {self.end_time:.2f}s)"


class ReviewCard(models.Model):
    """
    Spaced Repetition System (SRS) Card for an AudioSlice.
    Tracks the user's progress in translating or listening to this slice.
    """
    class BoxLevel(models.IntegerChoices):
        BOX_1 = 1, 'Box 1 (Daily)'
        BOX_2 = 2, 'Box 2 (Every 3 Days)'
        BOX_3 = 3, 'Box 3 (Weekly)'
        BOX_4 = 4, 'Box 4 (Bi-weekly)'
        BOX_5 = 5, 'Box 5 (Mastered)'

    class ReviewType(models.TextChoices):
        TRANSLATION = 'translation', 'Translation (CN -> EN)'
        LISTENING = 'listening', 'Listening (Audio -> EN)'

    audio_slice = models.OneToOneField(AudioSlice, on_delete=models.CASCADE, related_name='review_card')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    box_level = models.PositiveIntegerField(
        choices=BoxLevel.choices, 
        default=BoxLevel.BOX_1, 
        help_text="Leitner box level (1-5)"
    )
    next_review_date = models.DateField(help_text="When this card is due for review")
    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    
    review_type = models.CharField(
        max_length=20, 
        choices=ReviewType.choices, 
        default=ReviewType.TRANSLATION
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Review ({self.review_type}) for {self.audio_slice} - Level {self.box_level}"
