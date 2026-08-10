from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Textbook',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="教材名，如 '5A新版五上'", max_length=255)),
                ('grade', models.CharField(blank=True, default='', help_text='年级，如 \'五年级\'', max_length=50)),
                ('semester', models.CharField(blank=True, default='', help_text='学期，如 \'上册\'', max_length=50)),
                ('pdf_file', models.FileField(help_text='教材 PDF 文件', upload_to='textbooks/')),
                ('parsed_pages', models.JSONField(blank=True, default=None, help_text='全书页面文本数组缓存', null=True)),
                ('words_region_pages', models.JSONField(blank=True, default=None, help_text='书末词表区域页范围', null=True)),
                ('words_by_unit', models.JSONField(blank=True, default=None, help_text='词表按 Unit 归类结果 {unit: [words]}', null=True)),
                ('parsed_at', models.DateTimeField(blank=True, help_text='最近一次解析时间', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
