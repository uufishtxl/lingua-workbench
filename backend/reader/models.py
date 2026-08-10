from django.db import models
from django.conf import settings

class Book(models.Model):
    class Status(models.TextChoices):
        PROCESSING = 'processing', 'Processing'
        TRANSLATING = 'translating', 'Translating'
        READY = 'ready', 'Ready'
        FAILED = 'failed', 'Failed'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=500, blank=True, help_text="Book title extracted from PDF metadata or filename")
    author = models.CharField(max_length=255, blank=True, null=True, help_text="Book author")
    original_filename = models.CharField(max_length=500, help_text="Original PDF filename")
    pdf_file = models.FileField(upload_to='books/', help_text="Uploaded PDF file")
    
    # Reading progress tracking
    last_read_chapter = models.ForeignKey(
        'Chapter', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='+',
        help_text="Last read chapter"
    )
    last_read_paragraph_index = models.IntegerField(
        default=0, 
        help_text="Last read paragraph index within the chapter"
    )
    last_read_at = models.DateTimeField(
        null=True, 
        blank=True, 
        help_text="Last reading timestamp"
    )
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROCESSING)
    meta_context = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Metadata extracted from PDF (outline, domain, etc.)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title or self.original_filename} ({self.get_status_display()})"


class Chapter(models.Model):
    class Status(models.TextChoices):
        PROCESSING = 'processing', 'Processing'
        READY = 'ready', 'Ready'
        FAILED = 'failed', 'Failed'

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=500, help_text="Chapter title")
    chapter_index = models.IntegerField(db_index=True, help_text="Chapter order (0, 1, 2...)")
    start_page = models.IntegerField(help_text="Start page number in PDF")
    end_page = models.IntegerField(help_text="End page number in PDF")
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROCESSING)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['book', 'chapter_index']
        indexes = [models.Index(fields=['book', 'chapter_index'])]

    def __str__(self):
        return f"{self.book.title} - Chapter {self.chapter_index}: {self.title}"


class Article(models.Model):
    class Status(models.TextChoices):
        PROCESSING = 'processing', 'Processing'
        TRANSLATING = 'translating', 'Translating'
        READY = 'ready', 'Ready'
        FAILED = 'failed', 'Failed'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    url = models.CharField(max_length=1024, help_text="Original URL of the article")
    title = models.CharField(max_length=500, blank=True, help_text="Extracted title")
    author = models.CharField(max_length=255, blank=True, null=True)
    site_name = models.CharField(max_length=255, blank=True, null=True)
    raw_html = models.TextField(blank=True, help_text="Cleaned HTML from Readability.js")
    raw_text = models.TextField(blank=True, help_text="Plain text from Readability.js")
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROCESSING)
    meta_context = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Silently populated by LLM. Stores logic skeleton (outline) and domain attributes (domain, tone)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title or self.url} ({self.get_status_display()})"


class Paragraph(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='paragraphs', null=True, blank=True)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='paragraphs', null=True, blank=True)
    index = models.IntegerField(db_index=True, help_text="Sequential index of the paragraph (0, 1, 2...)")
    content = models.TextField(help_text="The text of the paragraph")
    translation = models.TextField(blank=True, help_text="The Chinese translated text of the paragraph")
    audio_url = models.CharField(max_length=500, blank=True, help_text="Relative path to TTS audio file")

    class Meta:
        ordering = ['article', 'chapter', 'index']
        indexes = [models.Index(fields=['article', 'index']), models.Index(fields=['chapter', 'index'])]

    def __str__(self):
        if self.article:
            return f"Article {self.article_id} - P{self.index}"
        elif self.chapter:
            return f"Chapter {self.chapter_id} - P{self.index}"
        return f"Paragraph {self.id}"


class Annotation(models.Model):
    class Type(models.TextChoices):
        YELLOW = 'yellow', 'Jargon (Yellow)'
        BLUE = 'blue', 'Usage (Blue)'
        PINK = 'pink', 'Thought (Pink)'

    paragraph = models.ForeignKey(Paragraph, on_delete=models.CASCADE, related_name='annotations')
    selected_text = models.TextField(help_text="The text selected by the user")
    user_note = models.TextField(blank=True, help_text="User's reflections/notes")
    annotation_type = models.CharField(
        max_length=20, 
        choices=Type.choices, 
        default=Type.YELLOW,
        help_text="Type of annotation which dictates the AI Copilot persona"
    )
    
    # Store AI response
    ai_response = models.JSONField(blank=True, null=True, help_text="Dynamic AI response based on annotation type")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.annotation_type}] {self.selected_text[:30]}"


