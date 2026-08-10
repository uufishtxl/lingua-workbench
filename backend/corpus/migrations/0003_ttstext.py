from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('corpus', '0002_corpustask'),
    ]

    operations = [
        migrations.CreateModel(
            name='TtsText',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('modules', models.JSONField(default=dict, help_text='{module_key: {text, sentences: [str]}}')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('task', models.OneToOneField(on_delete=models.CASCADE, related_name='tts_text', to='corpus.corpustask')),
            ],
        ),
    ]
