from rest_framework import serializers
from .models import PomodoroTag, Pomodoro

class PomodoroTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = PomodoroTag
        # fields = ['id', 'name', 'order']
        exclude = []

class PomodoroSerializer(serializers.ModelSerializer):
    tag = PomodoroTagSerializer(read_only=True) # 只供“读”，写的请求里不可以包含这个字段
    tag_id = serializers.PrimaryKeyRelatedField( # `PrimaryKeyRelatedField` 天生自带外键的 存在性校验（Exists Check） 和 对象转化 功能。只要加上 queryset，它就能把前端传来的冰冷数字，安全地翻译成后端所需的物理实体。
        queryset=PomodoroTag.objects.all(), source='tag', write_only=True # 只供“写”的请求时，可以包含这个字段
    )

    class Meta:
        model = Pomodoro
        fields = ['id', 'created_at', 'completed_at', 'duration', 'tag', 'tag_id', 'task', 'status', 'user'] # tag_id 是 write_only，因此在给前端的数据中，是没有这个字段的；tag 则是 read_only，因此在给前端的数据中，是包含这个字段的。
        read_only_fields = ['id', 'created_at', 'completed_at', 'user']
    
    def validate_duration(self, value): # validate_<field_name> 是 DRF 的一个钩子，用于对某个字段进行校验，可以直接获取到 value
        if value < 5:
            raise serializers.ValidationError("Duration must be at least 5 minutes")
        return value
