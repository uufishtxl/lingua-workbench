from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator

# --- 重写 Reader 小练习 --- START

class SArticle(models.Model):
    class Status(models.TextChoices):
        PROCESSING = 'processing', 'Processing'
        TRANSLATING = 'translating', 'Translating'
        READY = 'ready', 'Ready'
        FAILED = 'failed', 'Failed'
    
    # 字符串字段推荐只用 blank=True，除非该字段是可选的外键/数字
    title = models.CharField(max_length=500, blank=True, help_text="Title of the Article")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sarticles')
    url = models.URLField(max_length=1024, help_text="URL of the article")
    author = models.CharField(max_length=255, blank=True, null=True) 
    site_name = models.CharField(max_length=255, blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROCESSING)
    created_at = models.DateTimeField(auto_now_add=True, help_text="Created Time")
    # auto_now=True 确保每次 save() 时都会自动更新时间
    updated_at = models.DateTimeField(auto_now=True, help_text="Last Updated Time")
    
    # 文章正文往往很长，用 blank=True 允许暂时为空
    raw_text = models.TextField(blank=True, help_text="Raw text extracted from Readability.js")
    raw_html = models.TextField(blank=True, help_text="Raw html extracted from Readability.js")
    
    # JSONField 必须带 default=dict
    ai_context = models.JSONField(default=dict, blank=True, help_text="Article Meta Data from LLM")

    class Meta:
        ordering = ['-created_at'] # 修正：之前写成了冒号

    def __str__(self):
        return f"SArticle {self.title or self.url} on {self.created_at.strftime('%Y-%m-%d')}"
    
class SParagraph(models.Model):
    # 记得加上 models. 前缀
    article = models.ForeignKey(SArticle, on_delete=models.CASCADE, related_name='sparagraphs')
    # 既然下面已经有了复合索引，这里就不需要单独的 db_index=True 了
    index = models.IntegerField(help_text="Sequential index of the paragraph (0-based)") 
    content = models.TextField(help_text="The text of the paragraph")
    translation = models.TextField(blank=True, help_text="The Chinese translated text of the paragraph")

    class Meta:
        ordering = ['article', 'index']
        # 这个复合索引非常优秀，它能极大加速“获取某文章段落”的操作
        indexes = [models.Index(fields=['article', 'index'])]

    def __str__(self):
        return f"SParagraph {self.article_id} - P{self.index}"

class SAnnotation(models.Model):
    class Type(models.TextChoices):
        BLUE = 'blue', 'Usage (Blue)'
        PINK = 'pink', 'Thought (Pink)'  # 修正了 Pint 的拼写错误
        YELLOW = 'yellow', 'Jargon (Yellow)'

    paragraph = models.ForeignKey(SParagraph, on_delete=models.CASCADE, related_name="sannotations")
    selected_text = models.TextField(help_text="Text to explain")
    user_note = models.CharField(max_length=200, blank=True, help_text="User's comment")
    annotation_type = models.CharField(max_length=20, choices=Type.choices, default=Type.YELLOW)
    ai_response = models.JSONField(default=dict, blank=True, help_text="Dynamic AI response")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at'] # 标注通常希望看到最新的

    def __str__(self):
        return f"SAnnotation {self.paragraph_id} - {self.annotation_type}"



# --- 重写 Reader 小练习 --- END

# Create your models here.
class Author(models.Model):
    name = models.CharField(max_length=50, help_text="e.g., 'Johe Doe'")
    age = models.PositiveIntegerField()
    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=100, help_text="e.g., 'The Great Gatsby'")
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='books')
    def __str__(self):
        return self.title

# --- 重写 Pomodoro 练习 --- 

class PTagSandbox(models.Model):
    name = models.CharField(max_length=50, help_text="标签名")
    order = models.IntegerField(default=0, help_text="用于在 UI 矩阵中排序")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class PSandbox(models.Model):
    class Status(models.TextChoices):
        STARTED = 'started', 'Started'
        COMPLETED = 'completed', 'Completed'
        INTERRUPTED = 'interrupted', 'Interrupted'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='psandboxes')
    created_at = models.DateTimeField(auto_now_add=True, help_text="按下开始键的瞬间")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="专注真正结束的瞬间")
    duration = models.IntegerField(
        validators=[MinValueValidator(5)],
        help_text="设定的专注时长 (分钟)"
    )
    tag = models.ForeignKey(PTagSandbox, on_delete=models.PROTECT, related_name='psandboxes')
    task = models.CharField(max_length=500, blank=True, null=True, help_text="预留字段，日后手动补全专注细节")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.STARTED)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"PSandbox {self.duration}m [{self.tag.name}] on {self.created_at.strftime('%Y-%m-%d')}"
