import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scripts', '0007_alter_scriptline_order'),
        ('audio_slicer', '0006_audioslice_translation_alter_audioslice_is_idiom_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='RoughSliceTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('message', models.TextField(blank=True, default='')),
                ('slice_count', models.IntegerField(default=0, help_text='Number of rough slices created')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('chunk', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rough_slice_tasks', to='audio_slicer.audiochunk')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
