from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator

class PomodoroTag(models.Model):
    name = models.CharField(max_length=50, help_text="标签名")
    order = models.IntegerField(default=0, help_text="用于在 UI 矩阵中排序")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name

class Pomodoro(models.Model):
    class Status(models.TextChoices):
        STARTED = 'started', 'Started'
        COMPLETED = 'completed', 'Completed'
        INTERRUPTED = 'interrupted', 'Interrupted'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pomodoros')
    created_at = models.DateTimeField(auto_now_add=True, help_text="按下开始键的瞬间")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="专注真正结束的瞬间")
    duration = models.IntegerField(
        validators=[MinValueValidator(5)],
        help_text="设定的专注时长 (分钟)"
    )
    tag = models.ForeignKey(PomodoroTag, on_delete=models.PROTECT, related_name='pomodoros')
    task = models.CharField(max_length=500, blank=True, null=True, help_text="预留字段，日后手动补全专注细节")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.STARTED)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Pomodoro {self.duration}m [{self.tag.name}] on {self.created_at.strftime('%Y-%m-%d')}"
