from django.contrib import admin
from .models import Author, Book, PTagSandbox, PSandbox

# Register your models here.
admin.site.register(Author)
admin.site.register(Book)
admin.site.register(PTagSandbox)
admin.site.register(PSandbox)