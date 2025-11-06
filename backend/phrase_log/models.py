from django.db import models
from django.conf import settings

class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="e.g., 'Tech English', 'Daily Life'")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

# Create your models here.
class PhraseLog(models.Model):
    #    我们使用 settings.AUTH_USER_MODEL (最佳实践)
    #    on_delete=models.CASCADE: 如果用户被删除, 他所有的笔记也一起删除
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    original_context = models.CharField(max_length=500)
    expression_text = models.CharField(max_length=500)
    chinese_meaning = models.CharField(max_length=500)
    example_sentence = models.CharField(max_length=500)
    tags = models.ManyToManyField(Tag, blank=True) # blank=True 意味着这个短语“可以没有”标签
    tested = models.PositiveIntegerField(default=0, help_text="Count of times this was included in a quiz")
    failed = models.PositiveIntegerField(default=0, help_text="Count of times this was failed in a quiz")
    failed_radio = models.PositiveIntegerField(default=100, help_text="Ratio of failure. Defaults to 100 for untested items.")
    remark=models.CharField(null=True, blank=True, max_length=500)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.tested > 0:
            ratio = (self.failed / self.tested) * 100
            self.failed_radio = int(round(ratio))
        else:
            self.failed_radio = 100
        super().save(*args, **kwargs) # Call the "real" save() method.

    def __str__(self):
        return self.expression_text