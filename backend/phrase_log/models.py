from django.db import models

# Create your models here.
class PhraseLog(models.Model):
    original_context = models.CharField(max_length=500)
    expression_text = models.CharField(max_length=500)
    chinese_meaning = models.CharField(max_length=500)
    example_sentence = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.expression_text