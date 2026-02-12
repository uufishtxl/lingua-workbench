from django.db import migrations


def populate_order_from_index(apps, schema_editor):
    """Copy index value to order for all existing ScriptLine rows."""
    ScriptLine = apps.get_model('scripts', 'ScriptLine')
    # Use bulk update for efficiency 
    lines = ScriptLine.objects.filter(order__isnull=True)
    batch = []
    for line in lines.iterator(chunk_size=500):
        line.order = float(line.index)
        batch.append(line)
        if len(batch) >= 500:
            ScriptLine.objects.bulk_update(batch, ['order'])
            batch = []
    if batch:
        ScriptLine.objects.bulk_update(batch, ['order'])


class Migration(migrations.Migration):

    dependencies = [
        ('scripts', '0004_add_order_field'),
    ]

    operations = [
        migrations.RunPython(
            populate_order_from_index,
            migrations.RunPython.noop,  # reverse: do nothing
        ),
    ]
