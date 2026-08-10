from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import AudioSlice, ReviewCard, SourceAudio
from .services import slice_source_to_chunks

# English Book 教科书音频：脚本不走 fanfr.com 剧本抓取，直接从 corpus.TtsText 拼接。
# 与 TTS 音频生成一致（corpus/tasks.py 用 \"\\n\\n\".join(模块 text) 作为整段朗读文本）。
_TTS_MODULE_KEYS = ('fun_time', 'talking_time', 'story_time', 'project')


def _is_english_book(source_audio: SourceAudio) -> bool:
    """判断是否 English Book 教科书音频（drama 名包含 "English Book"）。"""
    return 'english book' in (source_audio.drama.name or '').lower()


def _get_tts_script_lines(source_audio: SourceAudio) -> list:
    """从 corpus.TtsText（task.unit == source_audio.episode）取清洁版（含换行）文字拼接为 script。

    返回逐行文本列表（每行一条 ScriptLine）。找不到 TtsText 时返回空列表。
    """
    from corpus.models import TtsText

    tts_text = (
        TtsText.objects
        .select_related('task')
        .filter(task__unit=source_audio.episode)
        .order_by('-created_at')
        .first()
    )
    if tts_text is None:
        return []

    parts = []
    for key in _TTS_MODULE_KEYS:
        module = (tts_text.modules or {}).get(key)
        if not isinstance(module, dict):
            continue
        text = (module.get('text') or '').strip()
        if text:
            parts.append(text)
    # 清洁版（含换行）文字拼接：模块间用空行分隔，与 TTS 整段朗读文本一致
    script = '\n\n'.join(parts)
    return [line.strip() for line in script.splitlines() if line.strip()]


def _ingest_tts_script(source_audio: SourceAudio) -> None:
    """English Book 专用：用 TtsText 清洁文本生成 ScriptLine（挂在第一个 chunk）。

    不走 fanfr.com 抓取。导入完成后入队 Huey 翻译任务（避免在请求线程里同步调 LLM），
    ScriptTask 状态由 worker 继续推进（translating → completed）。
    """
    from scripts.models import ScriptLine, ScriptTask
    from scripts.tasks import translate_script_lines_task
    from .models import AudioChunk

    script_task = ScriptTask.objects.create(
        source_audio=source_audio,
        status='ingesting',
        message=f'Building script from TtsText (Unit {source_audio.episode})...',
    )
    try:
        lines = _get_tts_script_lines(source_audio)
        if not lines:
            raise RuntimeError(f'No TtsText found for unit {source_audio.episode}.')

        first_chunk = AudioChunk.objects.filter(
            source_audio=source_audio
        ).order_by('chunk_index').first()
        if not first_chunk:
            raise RuntimeError('No audio chunks found for this source audio.')

        # 清掉旧行（重复上传/重跑时幂等）
        ScriptLine.objects.filter(chunk__source_audio=source_audio).delete()
        ScriptLine.objects.bulk_create([
            ScriptLine(
                chunk=first_chunk,
                index=i,
                order=float(i),
                line_type='dialogue',
                speaker='',
                text=line,
                raw_text=line,
            )
            for i, line in enumerate(lines)
        ])
        script_task.status = 'ingesting'
        script_task.ingest_count = len(lines)
        script_task.message = (
            f'Ingested {len(lines)} lines from TtsText (Unit {source_audio.episode}). '
            f'Starting translation...'
        )
        script_task.save()

        # 入队翻译任务（worker 里批量翻译 text_zh）
        translate_script_lines_task(script_task.id)
    except Exception as exc:
        script_task.status = 'failed'
        script_task.message = f'Script ingest from TtsText failed: {exc}'
        script_task.save()

@receiver(post_save, sender=AudioSlice)
def create_review_card_if_idiom(sender, instance, created, **kwargs):
    """
    Automatically create a ReviewCard if an AudioSlice is marked as an idiom (is_idiom=True).
    The card is scheduled for immediate review (next_review_date = today).
    """
    if instance.is_idiom:
        # Check if card already exists
        if not hasattr(instance, 'review_card'):
            # Determine review type based on translation availability
            # (Though logic can be dynamic in frontend, we set a reasonable default here)
            review_type = 'translation' if instance.translation else 'listening'
            
            ReviewCard.objects.create(
                audio_slice=instance,
                user=instance.audio_chunk.source_audio.user, # Inherit owner from parent Audio -> Source
                next_review_date=timezone.now().date(),      # Due immediately
                review_type=review_type
            )

@receiver(post_save, sender=SourceAudio)
def trigger_audio_slicing(sender, instance, created, **kwargs):
    """
    Trigger the slicing process when a SourceAudio is created (uploaded).
    After slicing, schedule a background task to ingest and translate the script.
    """
    if created:
        print(f"Triggering slice logic for SourceAudio: {instance.id}")
        slice_source_to_chunks(instance)

        # English Book 教科书音频特殊处理：脚本直接取自 corpus.TtsText 清洁文本
        # （task.unit == episode），不走 fanfr.com 剧本抓取。
        if _is_english_book(instance):
            print(f"English Book detected, ingesting script from TtsText for SourceAudio: {instance.id}")
            _ingest_tts_script(instance)
            return

        # Schedule background script ingest + translate task
        from scripts.models import ScriptTask
        from scripts.tasks import ingest_and_translate_script

        script_task = ScriptTask.objects.create(
            source_audio=instance,
            status='pending',
            message=f'Queued for S{instance.season:02d}E{instance.episode:02d}',
        )
        ingest_and_translate_script(script_task.id)
        print(f"Scheduled script ingest+translate task #{script_task.id} for SourceAudio: {instance.id}")
