from django.apps import AppConfig


class CorpusConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'corpus'
    verbose_name = 'Corpus Pipeline'

    def ready(self):
        # 注册 huey 任务（djhuey 靠 ready() 导入发现任务模块，缺失则 worker 无法执行）
        import corpus.tasks  # noqa: F401
