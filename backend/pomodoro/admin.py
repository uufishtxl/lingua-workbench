from django.contrib import admin
from .models import PomodoroTag, Pomodoro

admin.site.register(PomodoroTag)

@admin.register(Pomodoro)
class PomodoroAdmin(admin.ModelAdmin):
    # 这一行决写定了在“列表页”看到什么
    list_display = ('id', 'tag', 'duration', 'status', 'created_at', 'completed_at')
    
    # 【核心！】这一行告诉 Admin，即便这些字段不可编辑，也要在“详情页”显示出来
    readonly_fields = ('id', 'created_at', 'completed_at')
    
    # 增加右侧筛选栏，方便查找
    list_filter = ('tag', 'status')