from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reader', '0005_alter_paragraph_options_alter_paragraph_article_book_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='status',
            field=models.CharField(
                choices=[
                    ('processing', 'Processing'),
                    ('translating', 'Translating'),
                    ('ready', 'Ready'),
                    ('failed', 'Failed'),
                ],
                default='processing',
                max_length=20,
            ),
        ),
    ]