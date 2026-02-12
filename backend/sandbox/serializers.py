from rest_framework import serializers
from .models import Author

class AuthorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Author
        fields = '__all__'

    def validate_age(self, value):
        print(f">>> 1. 正在执行 validate_age: {value}")
        if value > 150:
            raise serializers.ValidationError("Age cannot be greater than 150")
        return value

    def validate(self, attrs):
        print(f">>> 2. 正在执行 validate 全局")
        name = attrs.get('name')
        age = attrs.get('age')
        if name == 'Child' and age >= 18:
            raise serializers.ValidationError("Child cannot be 18 or older")
        return attrs

    # 问题：serializers.Seriazlier 和 ModelSerializer 的区别？
    # 这里 attrs 是 Pydantic 数据类型吗？