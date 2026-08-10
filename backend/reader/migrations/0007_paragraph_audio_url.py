# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reader', '0006_add_translating_status_to_book'),
    ]

    operations = [
        migrations.AddField(
            model_name='paragraph',
            name='audio_url',
            field=models.CharField(blank=True, default='', help_text='Relative path to TTS audio file', max_length=500),
            preserve_default=False,
        ),
    ]
