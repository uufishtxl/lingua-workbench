import re

from rest_framework import serializers

from .models import CorpusTask, Textbook


class TextbookSerializer(serializers.ModelSerializer):
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = Textbook
        # parsed_pages / words_region_pages 是大体积缓存，不暴露到 API
        fields = [
            'id', 'name', 'grade', 'semester',
            'pdf_file', 'pdf_url', 'parsed_at', 'created_at',
        ]
        read_only_fields = ['pdf_url', 'parsed_at', 'created_at']

    def get_pdf_url(self, obj):
        if obj.pdf_file:
            return obj.pdf_file.url
        return None

    def validate_pdf_file(self, value):
        if value and not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError("仅支持 PDF 文件")
        if value and value.size > 100 * 1024 * 1024:
            raise serializers.ValidationError("文件不能超过 100MB")
        return value


class CorpusTaskSerializer(serializers.ModelSerializer):
    textbook_name = serializers.CharField(source='textbook.name', read_only=True)

    # ---- Stage 1 总览统计（#26，从已存产物计算，不落库） ----
    total_chars = serializers.SerializerMethodField()
    page_start = serializers.SerializerMethodField()
    page_end = serializers.SerializerMethodField()
    module_count = serializers.SerializerMethodField()
    words_count = serializers.SerializerMethodField()
    modules_present = serializers.SerializerMethodField()
    kp_progress = serializers.SerializerMethodField()

    class Meta:
        model = CorpusTask
        fields = [
            'id', 'name', 'textbook', 'textbook_name', 'unit',
            'status', 'stage', 'created_at', 'updated_at',
            'extract_status', 'extract_error',
            'bucket_status', 'bucket_error',
            'kp_status', 'kp_error',
            'tts_audio_url', 'tts_status', 'tts_error',
            'paper_status', 'paper_error',
            'total_chars', 'page_start', 'page_end', 'module_count', 'words_count',
            'modules_present', 'kp_progress',
            'knowledge_points',
        ]
        read_only_fields = [
            'name', 'status', 'stage', 'created_at', 'updated_at',
            'extract_status', 'extract_error',
            'bucket_status', 'bucket_error',
            'kp_status', 'kp_error',
            'tts_audio_url', 'tts_status', 'tts_error',
            'paper_status', 'paper_error',
            'total_chars', 'page_start', 'page_end', 'module_count', 'words_count',
            'modules_present', 'kp_progress',
        ]

    def get_total_chars(self, obj):
        if not obj.raw_pages:
            return 0
        return sum(len(p.get('text', '') or '') for p in obj.raw_pages)

    def get_page_start(self, obj):
        if not obj.raw_pages:
            return None
        return obj.raw_pages[0].get('page')

    def get_page_end(self, obj):
        if not obj.raw_pages:
            return None
        return obj.raw_pages[-1].get('page')

    def get_module_count(self, obj):
        if not obj.cleaned_modules:
            return 0
        return sum(1 for v in obj.cleaned_modules.values() if v)

    def get_words_count(self, obj):
        """Words to use 单词数：结构化格式取 items 长度，旧文本格式用正则。"""
        if not obj.cleaned_modules:
            return 0
        wt = obj.cleaned_modules.get('words_to_use')
        if isinstance(wt, dict):
            return len(wt.get('items') or [])
        if isinstance(wt, str):
            return len(re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)*", wt))
        return 0

    def get_modules_present(self, obj):
        """仅暴露模块键名（存在性），全文走 /corpus-tasks/{id}/modules/。"""
        if not obj.cleaned_modules:
            return []
        return [k for k, v in obj.cleaned_modules.items() if v]

    def get_kp_progress(self, obj):
        """知识点进度 x/7：非空板块数。"""
        if not obj.knowledge_points:
            return 0
        return sum(1 for v in obj.knowledge_points.values() if v)

    def create(self, validated_data):
        textbook = validated_data['textbook']
        unit = validated_data['unit']
        validated_data['name'] = f"{textbook.name} · Unit {unit}"
        return super().create(validated_data)
