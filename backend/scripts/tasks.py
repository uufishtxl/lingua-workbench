"""
Huey background tasks for script processing.
Handles script ingest (parsing from fanfr.com) and batch translation.
"""
import traceback
from huey.contrib.djhuey import task


@task()
def ingest_and_translate_script(script_task_id):
    """
    Background task: ingest a script from fanfr.com, then batch-translate it.

    Steps:
    1. Parse script HTML → create ScriptLine records
    2. Batch translate untranslated lines via DeepSeek
    3. Update ScriptTask status throughout

    Args:
        script_task_id: ID of the ScriptTask record to track progress
    """
    from .models import ScriptTask, ScriptLine
    from .parser import parse_fanfr_script
    from audio_slicer.models import AudioChunk
    from ai_analysis.services import batch_translate_idioms
    from django.db.models import Q

    try:
        script_task = ScriptTask.objects.get(id=script_task_id)
    except ScriptTask.DoesNotExist:
        return

    source_audio = script_task.source_audio
    season = source_audio.season
    episode = source_audio.episode

    # ========== Phase 1: Ingest ==========
    try:
        script_task.status = 'ingesting'
        script_task.message = f'Parsing script for S{season:02d}E{episode:02d}...'
        script_task.save()

        # Get the first chunk (scripts initially all go to chunk 1)
        first_chunk = AudioChunk.objects.filter(
            source_audio=source_audio
        ).order_by('chunk_index').first()

        if not first_chunk:
            script_task.status = 'failed'
            script_task.message = 'No audio chunks found for this source audio.'
            script_task.save()
            return

        # Parse the script from fanfr.com
        parsed_lines = parse_fanfr_script(season, episode)

        if not parsed_lines:
            script_task.status = 'failed'
            script_task.message = 'No script lines parsed from fanfr.com.'
            script_task.save()
            return

        # Clear existing script lines for this source audio (if re-ingesting)
        ScriptLine.objects.filter(chunk__source_audio=source_audio).delete()

        # Create script lines
        script_lines = []
        for idx, line_data in enumerate(parsed_lines):
            script_lines.append(ScriptLine(
                chunk=first_chunk,
                index=idx,
                line_type=line_data['type'],
                speaker=line_data.get('speaker'),
                text=line_data['text'],
                action_note=line_data.get('action_note'),
                raw_text=line_data['raw_text'],
            ))

        ScriptLine.objects.bulk_create(script_lines)
        script_task.ingest_count = len(script_lines)
        script_task.message = f'Ingested {len(script_lines)} lines. Starting translation...'
        script_task.save()

    except Exception as e:
        script_task.status = 'failed'
        script_task.message = f'Ingest failed: {str(e)}'
        script_task.save()
        traceback.print_exc()
        return

    # ========== Phase 2: Translate ==========
    try:
        script_task.status = 'translating'
        script_task.save()

        # Get lines without translation
        lines_to_translate = ScriptLine.objects.filter(
            chunk__source_audio=source_audio
        ).filter(
            Q(text_zh__isnull=True) | Q(text_zh__exact='')
        ).order_by('index')

        if not lines_to_translate.exists():
            script_task.status = 'completed'
            script_task.message = f'Ingested {script_task.ingest_count} lines. All already translated.'
            script_task.save()
            return

        # Batch translate (same logic as views.py translate action)
        BATCH_SIZE = 50
        total_translated = 0
        all_lines = list(lines_to_translate.values('id', 'text'))

        for i in range(0, len(all_lines), BATCH_SIZE):
            batch = all_lines[i:i + BATCH_SIZE]
            translations = batch_translate_idioms(batch)

            for item in translations:
                line_id = item.get('id')
                translation = item.get('translation')
                if line_id and translation:
                    ScriptLine.objects.filter(id=line_id).update(text_zh=translation)
                    total_translated += 1

            # Update progress
            script_task.translate_count = total_translated
            script_task.message = f'Translated {total_translated}/{len(all_lines)} lines...'
            script_task.save()

        script_task.status = 'completed'
        script_task.translate_count = total_translated
        script_task.message = (
            f'Done! Ingested {script_task.ingest_count} lines, '
            f'translated {total_translated} lines.'
        )
        script_task.save()

    except Exception as e:
        script_task.status = 'failed'
        script_task.message = f'Translation failed: {str(e)} (ingested {script_task.ingest_count} lines OK)'
        script_task.save()
        traceback.print_exc()
