from django.db import models

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