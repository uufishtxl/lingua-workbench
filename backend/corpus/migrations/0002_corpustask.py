from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('corpus', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CorpusTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="任务名，如 '5A新版五上 · Unit 2'", max_length=255)),
                ('unit', models.PositiveIntegerField()),
                ('status', models.CharField(choices=[('draft', '草稿'), ('proofreading', '校订中'), ('completed', '已完成')], default='draft', max_length=20)),
                ('stage', models.PositiveIntegerField(default=0, help_text='0-3')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('raw_pages', models.JSONField(blank=True, default=None, help_text='原始 page 级文本（不可变）', null=True)),
                ('cleaned_modules', models.JSONField(blank=True, default=None, help_text='6 模块清洗后文本', null=True)),
                ('knowledge_points', models.JSONField(blank=True, default=None, help_text='7 大知识点', null=True)),
                ('tts_audio_url', models.CharField(blank=True, default='', max_length=512)),
                ('tts_timestamps', models.JSONField(blank=True, default=None, null=True)),
                ('extract_status', models.CharField(choices=[('pending', '排队中'), ('running', '执行中'), ('done', '完成'), ('error', '失败')], default='pending', max_length=20)),
                ('extract_error', models.TextField(blank=True, default='')),
                ('bucket_status', models.CharField(choices=[('pending', '排队中'), ('running', '执行中'), ('done', '完成'), ('error', '失败')], default='pending', max_length=20)),
                ('bucket_error', models.TextField(blank=True, default='')),
                ('kp_status', models.CharField(choices=[('pending', '排队中'), ('running', '执行中'), ('done', '完成'), ('error', '失败')], default='pending', max_length=20)),
                ('kp_error', models.TextField(blank=True, default='')),
                ('tts_status', models.CharField(choices=[('pending', '排队中'), ('running', '执行中'), ('done', '完成'), ('error', '失败')], default='pending', max_length=20)),
                ('tts_error', models.TextField(blank=True, default='')),
                ('paper_status', models.CharField(choices=[('pending', '排队中'), ('running', '执行中'), ('done', '完成'), ('error', '失败')], default='pending', max_length=20)),
                ('paper_error', models.TextField(blank=True, default='')),
                ('textbook', models.ForeignKey(on_delete=models.PROTECT, related_name='tasks', to='corpus.textbook')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
