from django.db import models


class ScriptLine(models.Model):
    """
    剧本的一行，可以是对话、动作或场景标题。
    初始时全部挂载在该集第一个 Chunk 下，用户通过 "Split" 操作将后续行推给下一个 Chunk。
    """
    # --- 1. 定位与顺序 ---
    chunk = models.ForeignKey(
        'audio_slicer.AudioChunk',
        on_delete=models.CASCADE,
        related_name='script_lines',
        help_text="归属的 Chunk，初始全部指向该集第一个 Chunk"
    )
    index = models.IntegerField(db_index=True, help_text="原始导入顺序 (0, 1, 2...), 不可修改")
    order = models.FloatField(db_index=True, default=0, help_text="排序权重，支持小数插入 (1.5 = 在1和2之间)")

    # --- 2. 类型与内容 ---
    LINE_TYPES = [
        ('dialogue', 'Dialogue'),   # 有人说话
        ('action', 'Action'),       # 独立动作/旁白
        ('scene', 'Scene'),         # 场景标题 [Scene: ...]
    ]
    line_type = models.CharField(max_length=20, choices=LINE_TYPES, default='dialogue')

    speaker = models.CharField(max_length=100, null=True, blank=True, help_text="说话人 (仅 dialogue)")
    text = models.TextField(help_text="核心展示文本 (Clean Text，不含动作括号)")
    text_zh = models.TextField(null=True, blank=True, help_text="中文翻译")
    action_note = models.TextField(null=True, blank=True, help_text="附属动作 (dialogue 中穿插的括号内容)")
    raw_text = models.TextField(help_text="原始文本 (Backup)")

    # --- 3. 关联与状态 ---
    slice = models.ForeignKey(
        'audio_slicer.AudioSlice',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="弱关联到具体的 AudioSlice (点击查找后绑定)"
    )

    HIGHLIGHT_CHOICES = [
        ('none', 'None'),
        ('yellow', 'Review'),
        ('red', 'Hard'),
    ]
    highlight = models.CharField(
        max_length=20,
        choices=HIGHLIGHT_CHOICES, # 每一个元组都遵循固定格式 (存储值, 显示值)
        default='none',
        help_text="复习高亮"
    )

    class Meta:
        ordering = ['chunk', 'order']
        indexes = [models.Index(fields=['chunk', 'order'])]

    def __str__(self):
        if self.line_type == 'dialogue':
            return f"[{self.index}] {self.speaker}: {self.text[:30]}..."
        elif self.line_type == 'scene':
            return f"[{self.index}] Scene: {self.text[:30]}..."
        else:
            return f"[{self.index}] Action: {self.text[:30]}..."
    
    def __repr__(self):
        return f"ScriptLine(id={self.id}, index={self.index}, speaker={self.speaker}, text={self.text}), highlight={self.highlight}"


class ScriptTask(models.Model):
    """
    Tracks the status of a background script ingest + translate task.
    Created when a SourceAudio is uploaded; updated by the Huey worker.
    Frontend polls this to show progress notifications.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('ingesting', 'Ingesting Script'),
        ('translating', 'Translating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    source_audio = models.ForeignKey(
        'audio_slicer.SourceAudio',
        on_delete=models.CASCADE,
        related_name='script_tasks',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True, default='')
    ingest_count = models.IntegerField(default=0, help_text="Number of script lines ingested")
    translate_count = models.IntegerField(default=0, help_text="Number of lines translated")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"ScriptTask({self.source_audio}) - {self.status}"
