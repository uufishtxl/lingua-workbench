"""
Huey background tasks for script processing.
Handles script ingest (parsing from fanfr.com) and batch translation.
"""
import json
import os
import re
import time
import traceback
from difflib import SequenceMatcher

import requests
from huey.contrib.djhuey import task

WHISPER_BASE_URL = os.getenv("WHISPER_BASE_URL", "http://localhost:8001")
WHISPER_UPLOAD_TIMEOUT = 300      # whisper 上传/阻塞式转写超时（秒）
WHISPER_POLL_INTERVAL = 2.0       # 轮询转写任务间隔（秒）
WHISPER_POLL_MAX_ATTEMPTS = 300   # 最长约 10 分钟


# ---------------------------------------------------------------------------
# whisper 客户端：上传 chunk 音频 → 轮询 → 返回带时间戳的 segments
# ---------------------------------------------------------------------------

def _whisper_transcribe(audio_path: str) -> list:
    """把音频上传到本地 whisper 服务（skip_llm=true 返回纯 segments），轮询到完成。

    返回 [{text, start, end}, ...]。失败/超时抛异常。
    """
    with open(audio_path, 'rb') as f:
        resp = requests.post(
            f'{WHISPER_BASE_URL}/transcribe',
            params={'skip_llm': 'true'},
            files={'file': (os.path.basename(audio_path), f, 'audio/mpeg')},
            timeout=WHISPER_UPLOAD_TIMEOUT,
        )
        resp.raise_for_status()
        task_id = (resp.json() or {}).get('task_id')
    if not task_id:
        raise RuntimeError(f'whisper 未返回 task_id: {resp.text[:300]}')

    for _ in range(WHISPER_POLL_MAX_ATTEMPTS):
        status_resp = requests.get(f'{WHISPER_BASE_URL}/task/{task_id}', timeout=30)
        status_resp.raise_for_status()
        data = status_resp.json()
        if data.get('status') == 'completed':
            try:
                segments = json.loads(data.get('result') or '[]')
            except json.JSONDecodeError:
                segments = []
            return [s for s in segments if isinstance(s, dict)]
        if data.get('status') == 'failed':
            raise RuntimeError(f'whisper 转写失败: {(data.get("result") or "")[:300]}')
        time.sleep(WHISPER_POLL_INTERVAL)
    raise TimeoutError('whisper 转写超时')


# ---------------------------------------------------------------------------
# 脚本行 ↔ whisper segments 粗略对齐（贪心、按顺序；够用即可）
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    """小写 + 去标点 + 收缩空白，便于文本匹配。"""
    return re.sub(r"[^a-z0-9']+\s*", ' ', (text or '').lower()).strip()


def _char_times(segment: dict) -> list:
    """把段文本按字符比例插值到绝对时间轴。返回 len(text)+1 个时间点。"""
    text = _normalize(segment.get('text') or '')
    start = float(segment.get('start') or 0)
    end = float(segment.get('end') or start)
    n = len(text)
    if n == 0:
        return [start, max(end, start)]
    dur = max(end - start, 0.01)
    return [start + dur * i / n for i in range(n + 1)]


def _build_transcript(segments: list):
    """拼接所有段 → (full_text, char_times)；char_times[i] = 第 i 个字符的起始时间。"""
    chars, times, last_t = [], [], None
    for seg in segments:
        text = _normalize(seg.get('text') or '')
        if not text:
            continue
        ct = _char_times(seg)
        if chars:
            chars.append(' ')
            times.append(last_t)   # 段间空格映射到上一段结束时间
        for i, ch in enumerate(text):
            chars.append(ch)
            times.append(ct[i])
        last_t = ct[-1]
    if chars and last_t is not None:
        times.append(last_t)
    return ''.join(chars), times


def _match_line(full: str, line: str, pos: int, min_ratio: float = 0.4):
    """在 full 中从 pos 起找 line 的最靠左可接受匹配块，返回 (start_char, end_char) 或 None。"""
    sm = SequenceMatcher(None, line, full, autojunk=False)
    min_size = max(3, int(len(line) * min_ratio))
    best = None
    for _, b, size in sm.get_matching_blocks():
        if size < min_size or b < pos:
            continue
        if best is None or b < best[0]:
            best = (b, size)
    if best is None:
        return None
    b, size = best
    return b, b + size


def align_lines_to_segments(lines: list, segments: list) -> list:
    """把 script 行与 whisper segments 粗略对齐（贪心、保持先后顺序）。

    返回 [(start, end), ...]（秒，已 round 3 位）；未匹配的行返回 None。
    """
    full, times = _build_transcript(segments)
    if not full:
        return [None] * len(lines)

    results = []
    pos = 0
    for line in lines:
        n_line = _normalize(line)
        if not n_line:
            results.append(None)
            continue
        m = _match_line(full, n_line, pos)
        if m is None:
            results.append(None)
            continue
        start_char, end_char = m
        start = times[start_char]
        end = times[min(end_char, len(times) - 1)]
        if end <= start:
            end = start + 0.2
        results.append((round(start, 3), round(end, 3)))
        pos = max(pos, end_char)
    return results


# ---------------------------------------------------------------------------
# Rough 切割主流程 + Huey 任务（ScriptPanel「连接」按钮触发）
# ---------------------------------------------------------------------------

ROUGH_SLICE_SOURCE = 'whisper_rough'   # AudioSlice.source 标记，重跑时幂等覆盖


def rough_slice_chunk(chunk_id: int) -> dict:
    """whisper 转写 chunk 音频 → 按该 chunk 的 Script 对齐 → 生成 rough AudioSlice 并绑定 ScriptLine。

    幂等：会先删除该 chunk 之前由本功能生成的 slices（source='whisper_rough'）再重建。
    返回 {'created', 'total_lines', 'segments'}。
    """
    from django.db import IntegrityError

    from .models import RoughSliceTask, ScriptLine
    from audio_slicer.models import AudioChunk, AudioSlice

    task_obj, _ = RoughSliceTask.objects.get_or_create(
        chunk_id=chunk_id,
        defaults={'status': 'running', 'message': '准备 whisper 转写...'},
    )
    if task_obj.status != 'running':
        task_obj.status = 'running'
        task_obj.message = '准备 whisper 转写...'
        task_obj.save(update_fields=['status', 'message'])

    try:
        chunk = AudioChunk.objects.prefetch_related('script_lines').get(id=chunk_id)
        lines = list(chunk.script_lines.all().order_by('order', 'index'))
        if not lines:
            raise RuntimeError('该 chunk 没有 ScriptLine，无法 rough 切割。')

        task_obj.message = 'whisper 转写音频中...'
        task_obj.save(update_fields=['message'])

        segments = _whisper_transcribe(chunk.file.path)

        task_obj.message = f'对齐 {len(lines)} 行脚本与 {len(segments)} 个转写段...'
        task_obj.save(update_fields=['message'])

        ranges = align_lines_to_segments([line.text for line in lines], segments)

        # 删除旧的 rough slices（关联的 ScriptLine.slice 自动置空）
        AudioSlice.objects.filter(audio_chunk=chunk, source=ROUGH_SLICE_SOURCE).delete()

        created_count = 0
        for line, rng in zip(lines, ranges):
            if rng is None:
                continue
            start, end = rng
            try:
                sl = AudioSlice.objects.create(
                    audio_chunk=chunk,
                    start_time=start,
                    end_time=end,
                    original_text=line.text,
                    source=ROUGH_SLICE_SOURCE,
                )
            except IntegrityError:
                sl = AudioSlice.objects.get(audio_chunk=chunk, start_time=start, end_time=end)
            if line.slice_id != sl.id:
                line.slice = sl
                line.save(update_fields=['slice'])
            created_count += 1

        if not chunk.has_slices:
            chunk.has_slices = True
            chunk.save(update_fields=['has_slices'])

        task_obj.status = 'completed'
        task_obj.slice_count = created_count
        task_obj.message = (
            f'完成：{len(lines)} 行脚本 → {created_count} 个 rough slices'
            f'（whisper {len(segments)} 段）。'
        )
        task_obj.save()
        return {'created': created_count, 'total_lines': len(lines), 'segments': len(segments)}
    except Exception as exc:  # noqa: BLE001
        task_obj.status = 'failed'
        task_obj.message = f'rough 切割失败: {exc}'
        task_obj.save()
        raise


@task()
def rough_slice_chunk_task(chunk_id: int):
    """Huey 入口：ScriptPanel「连接」按钮触发的 whisper rough 切割。"""
    return rough_slice_chunk(chunk_id)


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
        _translate_script_lines(script_task)
    except Exception as e:
        script_task.status = 'failed'
        script_task.message = f'Translation failed: {str(e)} (ingested {script_task.ingest_count} lines OK)'
        script_task.save()
        traceback.print_exc()


def _translate_script_lines(script_task) -> int:
    """批量翻译 script_task.source_audio 下所有未翻译的 ScriptLine（fanfr 与 TtsText 路径共用）。

    更新 ScriptTask 状态/进度；返回翻译的行数。
    """
    from django.db.models import Q
    from .models import ScriptLine
    from ai_analysis.services import batch_translate_texts

    source_audio = script_task.source_audio
    lines_to_translate = ScriptLine.objects.filter(
        chunk__source_audio=source_audio
    ).filter(
        Q(text_zh__isnull=True) | Q(text_zh__exact='')
    ).order_by('index')

    if not lines_to_translate.exists():
        script_task.status = 'completed'
        script_task.message = f'Ingested {script_task.ingest_count} lines. All already translated.'
        script_task.save()
        return 0

    # Batch translate (same logic as views.py translate action)
    BATCH_SIZE = 50
    total_translated = 0
    all_lines = list(lines_to_translate.values('id', 'text'))

    for i in range(0, len(all_lines), BATCH_SIZE):
        batch = all_lines[i:i + BATCH_SIZE]
        translations = batch_translate_texts(batch)

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
    return total_translated


@task()
def translate_script_lines_task(script_task_id: int):
    """Huey 入口：翻译 ScriptTask 对应 source audio 下未翻译的 ScriptLine（English Book 用）。"""
    from .models import ScriptTask

    try:
        script_task = ScriptTask.objects.get(id=script_task_id)
    except ScriptTask.DoesNotExist:
        return
    try:
        script_task.status = 'translating'
        script_task.message = 'Starting translation...'
        script_task.save()
        _translate_script_lines(script_task)
    except Exception as e:
        script_task.status = 'failed'
        script_task.message = f'Translation failed: {str(e)} (ingested {script_task.ingest_count} lines OK)'
        script_task.save()
        traceback.print_exc()
