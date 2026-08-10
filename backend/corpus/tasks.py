"""
Huey 任务：extract_unit —— Stage 0 提取主链（设计共识 §9）。

流程：全书解析缓存（首次）→ Unit 页提取 → 机械清洗 → 机械粗分桶 → 词表区域缓存。
raw_pages 为原始 page 级文本，永不被清洗/分桶覆盖。
"""
import logging
import os
import re

from django.utils import timezone
from huey.contrib.djhuey import db_task

logger = logging.getLogger(__name__)

from .llm import MODULE_KEYS, MAX_INPUT_CHARS, add_ipa_to_vocabulary, bucket_modules_with_llm, generate_kp_summary
from .models import CorpusTask, TtsText
from .tts import (
    build_tts_text,
    convert_audio_to_mp3,
    generate_learning_audio,
)
from .services import (
    bucket_modules,
    clean_text,
    extract_pages,
    has_text_layer,
    locate_unit_range,
    locate_words_region,
)


class ExtractionError(Exception):
    pass


@db_task()
def extract_unit_task(task_id: int):
    """huey 入口：直接调用 = 入队（immediate=False）；测试走 _run_extract_unit。"""
    return _run_extract_unit(task_id)


def _run_extract_unit(task_id: int):
    """提取主链（纯函数，测试直接调用；避免依赖 huey 执行模式）。"""
    task = CorpusTask.objects.select_related('textbook').get(id=task_id)
    task.extract_status = CorpusTask.TaskStatus.RUNNING
    task.save(update_fields=['extract_status'])
    logger.info(f"[corpus] extract_unit start: task={task_id}")

    try:
        textbook = task.textbook
        pdf_path = textbook.pdf_file.path

        # 1. 全书解析缓存（每本教材只解析一次）
        if not textbook.parsed_pages:
            # 文本层检测仅作软警告（trials 同款逻辑，误报率高；真正的校验看提取结果）
            if has_text_layer(pdf_path) == 0:
                task.extract_error += "警告：未检测到文本层操作符，若提取为空请检查是否扫描版。\n"
            pages = extract_pages(pdf_path)
            non_empty = [t for t in pages if t and t.strip()]
            if not non_empty:
                raise ExtractionError("PDF 文本提取结果为空，疑似扫描版，需要 OCR")
            textbook.parsed_pages = [{"page": i + 1, "text": t} for i, t in enumerate(pages)]
            textbook.parsed_at = timezone.now()
            textbook.save(update_fields=['parsed_pages', 'parsed_at'])

        page_dicts = textbook.parsed_pages
        pages = [p["text"] for p in page_dicts]

        # 2. Unit 范围定位
        rng, error, warnings = locate_unit_range(pages, task.unit)
        if rng is None:
            raise ExtractionError(error)
        start_idx, end_idx = rng

        # 3. 组装原始 page 文本（不可变）
        included = page_dicts[start_idx:end_idx]
        task.raw_pages = included

        # 起点页从 "Unit N" 关键字处截取，去掉页眉前缀
        pat_start = re.compile(rf"\bUnit\s*{task.unit}\b", re.IGNORECASE)
        first_text = included[0]["text"]
        m = pat_start.search(first_text)
        if m:
            first_text = first_text[m.start():]
        raw_text = "\n\n".join([first_text] + [p["text"] for p in included[1:]])

        # 4. 机械清洗 + 粗分桶
        cleaned, removed = clean_text(raw_text)
        task.cleaned_modules = bucket_modules(cleaned)
        logger.info(f"[corpus] unit={task.unit} cleaned chars={len(cleaned)} removed_numbers={removed}")

        # 5. 词表区域定位（缓存到 textbook，LLM 按 Unit 归类在 S5/S13 处理）
        if not textbook.words_region_pages:
            region = locate_words_region(pages)
            if region:
                textbook.words_region_pages = {
                    "start_page": region[0] + 1,
                    "end_page_exclusive": region[1] + 1,
                }
                textbook.save(update_fields=['words_region_pages'])
            else:
                task.extract_error += "警告：未定位到书末词表区域，词汇将仅来自 Topic words。\n"

        task.extract_status = CorpusTask.TaskStatus.DONE
        task.stage = 1
        task.extract_error = "\n".join(warnings) if warnings else task.extract_error
        task.save(update_fields=[
            'raw_pages', 'cleaned_modules', 'extract_status', 'stage', 'extract_error',
        ])
        logger.info(f"[corpus] extract_unit done: task={task_id} stage=1")

    except Exception as exc:  # noqa: BLE001
        logger.exception(f"[corpus] extract_unit failed: task={task_id}")
        task.extract_status = CorpusTask.TaskStatus.ERROR
        task.extract_error = str(exc)[:2000]
        task.save(update_fields=['extract_status', 'extract_error'])


def _module_to_text(val):
    """把模块内容拍平成文本（兼容结构化 dict 与纯文本），供 LLM 归整输入。"""
    if isinstance(val, str):
        return val
    if isinstance(val, dict):
        parts = []
        if val.get("title"):
            parts.append(val["title"])
        if val.get("content"):
            parts.append(val["content"])
        if val.get("sound"):
            parts.append(val["sound"])
        if val.get("grammar_tip"):
            parts.append(val["grammar_tip"])
        for sec in val.get("sections") or []:
            if sec.get("title"):
                parts.append(sec["title"])
            for step in sec.get("steps") or []:
                step_text = f"{step.get('title', '')} {step.get('content', '')}".strip()
                if step_text:
                    parts.append(step_text)
        return "\n".join(p for p in parts if p)
    return ""


def _extract_word_items(m):
    """兼容结构化 items 与旧文本格式（/ 或逗号分隔）的单词提取。过滤模块标题行与页码。"""
    _skip = {
        "topic words", "words to use", "fun time", "chant time", "rhyme time",
        "talking time", "story time", "reading time", "project", "sound",
        "find the rule", "quick tip", "big task", "title",
    }
    if isinstance(m, dict):
        return list(m.get('items') or [])
    if isinstance(m, str):
        out = []
        for w in re.split(r'[/,，、\n]', m):
            w = w.strip()
            if not w or w.isdigit() or w.lower() in _skip:
                continue
            out.append(w)
        return out
    return []


@db_task()
def llm_bucket_task(task_id: int):
    """huey 入口：机械粗分桶 → DeepSeek 归整为精准 6 模块（#27）。"""
    return _run_llm_bucket(task_id)


def _run_llm_bucket(task_id: int):
    """归整主链（测试直接调用，避免依赖 huey 执行模式）。"""
    try:
        task = CorpusTask.objects.select_related('textbook').get(id=task_id)
    except CorpusTask.DoesNotExist:
        logger.warning(f"[corpus] llm_bucket: task {task_id} 不存在，跳过")
        return

    task.bucket_status = CorpusTask.TaskStatus.RUNNING
    task.save(update_fields=['bucket_status'])
    logger.info(f"[corpus] llm_bucket start: task={task_id}")

    try:
        # 归整前保留机械分桶原始模块（LLM 丢失时兜底用，比词表准确，来自正文）
        original_modules = task.cleaned_modules or {}

        # 1. 组装输入：机械粗分桶的非空模块 + 词表区域原文（LLM 从中提取本单元词表）
        raw = []
        for key in MODULE_KEYS:
            val = original_modules.get(key)
            if val:
                raw.append(_module_to_text(val))

        words_text = ""
        textbook = task.textbook
        region = textbook.words_region_pages
        if region and textbook.parsed_pages:
            start = region.get("start_page", 1) - 1
            end = region.get("end_page_exclusive", len(textbook.parsed_pages)) - 1
            slice_pages = textbook.parsed_pages[start:end]
            words_text = "\n\n".join(p.get("text", "") for p in slice_pages).strip()

        text = "\n\n".join(raw).strip()
        if not text:
            raise ExtractionError("没有可归整的模块文本（机械粗分桶为空）")

        truncated = False
        if len(text) > MAX_INPUT_CHARS:
            text = text[:MAX_INPUT_CHARS]
            truncated = True

        # 2. LLM 归整
        modules = bucket_modules_with_llm(text, words_text or "（无）", task.unit)

        # 3. 写回 cleaned_modules（保留 6 键顺序，缺失为 None）
        ordered = {k: modules.get(k) for k in MODULE_KEYS}

        # topic_words / words_to_use 双向兜底：两个词汇模块至少一个有值
        # 优先级：机械分桶原始值（来自正文，最准）> 词表填充 > 留空
        tp = ordered.get('topic_words')
        wtu = ordered.get('words_to_use')
        if not tp and original_modules.get('topic_words'):
            ordered['topic_words'] = {
                "title": "Topic Words",
                "items": _extract_word_items(original_modules['topic_words']),
            }
            tp = ordered['topic_words']
        if not tp and isinstance(wtu, dict) and wtu.get('items'):
            ordered['topic_words'] = {"title": "Topic Words", "items": list(wtu.get('items') or [])}
        if not wtu and isinstance(tp, dict) and tp.get('items'):
            ordered['words_to_use'] = {"title": "Words to use", "items": list(tp.get('items') or [])}

        task.cleaned_modules = ordered
        task.bucket_status = CorpusTask.TaskStatus.DONE
        task.bucket_error = "输入超过 50000 字符已截断" if truncated else ""
        task.save(update_fields=['cleaned_modules', 'bucket_status', 'bucket_error'])
        logger.info(f"[corpus] llm_bucket done: task={task_id} modules={sum(1 for v in ordered.values() if v)}/6")

        # 链式触发 KP 预填（#28）：归整成功后自动入队
        generate_kps_task(task_id)

    except Exception as exc:  # noqa: BLE001
        logger.exception(f"[corpus] llm_bucket failed: task={task_id}")
        task.bucket_status = CorpusTask.TaskStatus.ERROR
        task.bucket_error = str(exc)[:2000]
        task.save(update_fields=['bucket_status', 'bucket_error'])




@db_task()
def generate_kps_task(task_id: int):
    """huey 入口：基于归整后的 cleaned_modules 预填 7 大知识点（#28）。"""
    return _run_generate_kps(task_id)


def _run_generate_kps(task_id: int):
    """KP 预填主链：规则提取（词汇/语法/拼读/范文）+ LLM 梗概（中文）。"""
    try:
        task = CorpusTask.objects.select_related('textbook').get(id=task_id)
    except CorpusTask.DoesNotExist:
        logger.warning(f"[corpus] generate_kps: task {task_id} 不存在，跳过")
        return

    task.kp_status = CorpusTask.TaskStatus.RUNNING
    task.save(update_fields=['kp_status'])
    logger.info(f"[corpus] generate_kps start: task={task_id}")

    try:
        mods = task.cleaned_modules or {}

        # 词汇：topic_words + words_to_use 合并去重（Q2 共识）
        words = []
        for key in ("topic_words", "words_to_use"):
            words.extend(_extract_word_items(mods.get(key)))
        seen = []
        for w in words:
            w = (w or "").strip()
            if w and w not in seen:
                seen.append(w)

        # 词汇：单词（非短语）补 IPA 音标；LLM 失败回退规则文本（"/" 分隔）
        vocabulary = " / ".join(seen)
        if seen:
            ipa_text = add_ipa_to_vocabulary(seen)
            if ipa_text:
                vocabulary = ipa_text

        kp = {
            "vocabulary": vocabulary,
            "phrases": "",
            "sentence_patterns": "",
            "grammar": "",
            "phonics": "",
            "summary": "",
            "big_task": "",
        }

        # 语法：Find the rule / Quick tip
        tt = mods.get("talking_time")
        if isinstance(tt, dict) and tt.get("grammar_tip"):
            kp["grammar"] = tt["grammar_tip"]
        # 拼读：Sound
        ft = mods.get("fun_time")
        if isinstance(ft, dict) and ft.get("sound"):
            kp["phonics"] = ft["sound"]
        # Big Task 范文：Project 范文正文
        pr = mods.get("project")
        if isinstance(pr, dict) and pr.get("content"):
            kp["big_task"] = pr["content"]
        # 梗概：Story time → LLM 中文梗概
        st = mods.get("story_time")
        story = st.get("content") if isinstance(st, dict) else (st if isinstance(st, str) else "")
        if story:
            kp["summary"] = generate_kp_summary(story)

        task.knowledge_points = kp
        task.kp_status = CorpusTask.TaskStatus.DONE
        task.save(update_fields=['knowledge_points', 'kp_status'])
        logger.info(f"[corpus] generate_kps done: task={task_id}")

    except Exception as exc:  # noqa: BLE001
        logger.exception(f"[corpus] generate_kps failed: task={task_id}")
        task.kp_status = CorpusTask.TaskStatus.ERROR
        task.kp_error = str(exc)[:2000]
        task.save(update_fields=['kp_status', 'kp_error'])


@db_task()
def generate_tts_task(task_id: int):
    """huey 入口：四模块整段 Gemini TTS + whisper 时间戳对齐（#33）。"""
    return _run_generate_tts(task_id)


def _run_generate_tts(task_id: int):
    """TTS：提取朗读文本 → Gemini 合成 → MP3 落盘（不做自动切割/对齐）。

    单次生成缓存复用（已有 tts_audio_url 不重复生成）；Topic words/Words to use 无音频。
    生成结果（无时间戳）：tts_audio_url 指向 MP3，可直接整段播放；
    音频文件位置：MEDIA_ROOT/{tts_audio_url}。
    """
    from django.conf import settings

    try:
        task = CorpusTask.objects.select_related('textbook').get(id=task_id)
    except CorpusTask.DoesNotExist:
        logger.warning(f"[corpus] generate_tts: task {task_id} 不存在，跳过")
        return

    if task.tts_audio_url:
        logger.info(f"[corpus] generate_tts: task {task_id} 已有音频，跳过（缓存复用）")
        task.tts_status = CorpusTask.TaskStatus.DONE
        task.save(update_fields=['tts_status'])
        return

    task.tts_status = CorpusTask.TaskStatus.RUNNING
    task.save(update_fields=['tts_status'])
    logger.info(f"[corpus] generate_tts start: task={task_id}")

    try:
        mods = task.cleaned_modules or {}

        # 1. 跟读专用文本分割（过滤 grammar_tip / B/Step 子章节 / "--" 残留行）
        module_texts = build_tts_text(mods)
        if not module_texts:
            raise ExtractionError("没有可生成音频的模块文本（Fun/Talking/Story/Project 均为空）")

        # 保存跟读专用文本结构（DB 表，学习页/后续复用）
        TtsText.objects.update_or_create(
            task=task,
            defaults={"modules": module_texts},
        )

        # 2. Gemini TTS 整段音频
        full_text = "\n\n".join(v["text"] for v in module_texts.values())
        rel_url = generate_learning_audio(full_text, task_id)
        audio_path = os.path.join(settings.MEDIA_ROOT, rel_url)
        if not os.path.exists(audio_path):
            raise ExtractionError(f"TTS 音频文件未找到: {audio_path}")

        # 3. 播放用 MP3（130s 大 WAV 浏览器 seek 不可靠 → 转 MP3）
        play_url = convert_audio_to_mp3(rel_url)

        # 转 TTS 即结束：不做自动切割/对齐（质量不稳定），时间戳留空
        task.tts_audio_url = play_url
        task.tts_timestamps = None
        task.tts_status = CorpusTask.TaskStatus.DONE
        task.save(update_fields=['tts_audio_url', 'tts_timestamps', 'tts_status'])
        logger.info(f"[corpus] generate_tts done: task={task_id} audio={play_url}")

    except Exception as exc:  # noqa: BLE001
        logger.exception(f"[corpus] generate_tts failed: task={task_id}")
        task.tts_status = CorpusTask.TaskStatus.ERROR
        task.tts_error = str(exc)[:2000]
        task.save(update_fields=['tts_status', 'tts_error'])

    except Exception as exc:  # noqa: BLE001
        logger.exception(f"[corpus] generate_tts failed: task={task_id}")
        task.tts_status = CorpusTask.TaskStatus.ERROR
        task.tts_error = str(exc)[:2000]
        task.save(update_fields=['tts_status', 'tts_error'])
