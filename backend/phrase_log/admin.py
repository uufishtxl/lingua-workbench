from django.contrib import admin
from .models import PhraseLog, Tag # , SourceAudio

# Register your models here.
admin.site.register(PhraseLog)
admin.site.register(Tag)
# admin.site.register(SourceAudio)
