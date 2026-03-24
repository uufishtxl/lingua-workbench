from django.contrib import admin
from .models import SourceAudio, AudioSlice, AudioChunk, AudioTag, Drama, ReviewCard

# Register your models here.
admin.site.register(SourceAudio)
admin.site.register(AudioSlice)
admin.site.register(AudioChunk)
admin.site.register(AudioTag)
admin.site.register(Drama)
admin.site.register(ReviewCard)
