from django.contrib import admin
from .models import PhraseLog
from .models import Tag

# Register your models here.
admin.site.register(PhraseLog)
admin.site.register(Tag)