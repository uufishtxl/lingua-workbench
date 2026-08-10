from django.db import models


class Textbook(models.Model):
    """
    教材实体：全局共享（个人项目，不按用户隔离）。

    设计共识 §1.1：
    - pdf_file 上传到 media/textbooks/
    - parsed_pages / words_region_pages / words_by_unit 为解析缓存
      （pdfplumber 一次解析，后续 Unit 任务复用；首次解析在 S2 extract_unit 任务触发）
    """
    name = models.CharField(max_length=255, help_text="教材名，如 '5A新版五上'")
    grade = models.CharField(max_length=50, blank=True, default='', help_text="年级，如 '五年级'")
    semester = models.CharField(max_length=50, blank=True, default='', help_text="学期，如 '上册'")

    pdf_file = models.FileField(upload_to='textbooks/', help_text="教材 PDF 文件")

    # ---- 解析缓存（S2 提取任务首次解析后填充，本切片暂不使用） ----
    parsed_pages = models.JSONField(null=True, blank=True, default=None, help_text="全书页面文本数组缓存")
    words_region_pages = models.JSONField(null=True, blank=True, default=None, help_text="书末词表区域页范围")
    words_by_unit = models.JSONField(null=True, blank=True, default=None, help_text="词表按 Unit 归类结果 {unit: [words]}")
    parsed_at = models.DateTimeField(null=True, blank=True, help_text="最近一次解析时间")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        parts = [self.grade, self.semester, self.name]
        label = ' '.join(p for p in parts if p)
        return label or self.name


class CorpusTask(models.Model):
    """
    语料加工任务（设计共识 §1.2 / §2 状态机）。

    - raw_pages: 原始 page 级提取文本，永不被清洗/分桶覆盖
    - cleaned_modules: 6 模块清洗后文本（S5 LLM 归整的输入/产物）
    - knowledge_points: 7 大知识点（S6 接入）
    - 各 *_status/*_error: 阶段任务状态（pending/running/done/error），前端轮询
    """

    class Status(models.TextChoices):
        DRAFT = 'draft', '草稿'
        PROOFREADING = 'proofreading', '校订中'
        COMPLETED = 'completed', '已完成'

    class TaskStatus(models.TextChoices):
        PENDING = 'pending', '排队中'
        RUNNING = 'running', '执行中'
        DONE = 'done', '完成'
        ERROR = 'error', '失败'

    name = models.CharField(max_length=255, help_text="任务名，如 '5A新版五上 · Unit 2'")
    textbook = models.ForeignKey(Textbook, on_delete=models.PROTECT, related_name='tasks')
    unit = models.PositiveIntegerField()

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    stage = models.PositiveIntegerField(default=0, help_text="0-3")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ---- 阶段产物 ----
    raw_pages = models.JSONField(null=True, blank=True, default=None, help_text="原始 page 级文本（不可变）")
    cleaned_modules = models.JSONField(null=True, blank=True, default=None, help_text="6 模块清洗后文本")
    knowledge_points = models.JSONField(null=True, blank=True, default=None, help_text="7 大知识点")
    tts_audio_url = models.CharField(max_length=512, blank=True, default='')
    tts_timestamps = models.JSONField(null=True, blank=True, default=None)

    # ---- 阶段任务状态 ----
    extract_status = models.CharField(max_length=20, choices=TaskStatus.choices, default=TaskStatus.PENDING)
    extract_error = models.TextField(blank=True, default='')
    bucket_status = models.CharField(max_length=20, choices=TaskStatus.choices, default=TaskStatus.PENDING)
    bucket_error = models.TextField(blank=True, default='')
    kp_status = models.CharField(max_length=20, choices=TaskStatus.choices, default=TaskStatus.PENDING)
    kp_error = models.TextField(blank=True, default='')
    tts_status = models.CharField(max_length=20, choices=TaskStatus.choices, default=TaskStatus.PENDING)
    tts_error = models.TextField(blank=True, default='')
    paper_status = models.CharField(max_length=20, choices=TaskStatus.choices, default=TaskStatus.PENDING)
    paper_error = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} (stage={self.stage}, {self.status})"


class TtsText(models.Model):
    """跟读专用文本结构（#33 增强）：独立于 cleaned_modules 的分割。

    从归整模块中提取"朗读内容"（排除 Find the rule 语法点、Project 的 B/Step 子章节、
    "--" 角色名占位行），按模块保存句子列表。TTS 拼接、whisper 对齐、学习页展示都基于它。
    """
    task = models.OneToOneField(CorpusTask, on_delete=models.CASCADE, related_name='tts_text')
    modules = models.JSONField(default=dict, help_text='{module_key: {text, sentences: [str]}}')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"TtsText(task={self.task_id})"
