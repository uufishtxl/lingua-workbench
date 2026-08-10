"""
语料提取服务（设计共识 §4 Stage 0 / §6 词表策略）。

职责（纯函数为主，便于 fixture 单测；PDF 解析层在容器外运行）：
  1. extract_pages / has_text_layer —— PDF 文本提取（pdfplumber 优先，回退 pypdf）
  2. locate_unit_range —— 按 "Unit N" ~ "Unit N+1" 关键字切页范围
  3. clean_text —— 机械清洗（删孤立页码、智能接回断行）
  4. bucket_modules —— 机械粗分桶（按模块标题锚点切割 6 模块，允许缺失）
  5. locate_words_region —— 书末词表区域定位（排除前 1/4 目录页）

说明：粗分桶是"粗"的（机械锚点），精准归整交给 S5 的 LLM 任务。
"""
import logging
import re
import zlib
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PDF 文本提取
# ---------------------------------------------------------------------------


def _col_text(col) -> str:
    """把一栏的词按行重组（top 分桶 + x0 排序）为文本。"""
    buckets = defaultdict(list)
    for w in col:
        buckets[round(w["top"] / 5)].append(w)
    lines = []
    for k in sorted(buckets):
        line = " ".join(w["text"] for w in sorted(buckets[k], key=lambda w: w["x0"]))
        if line.strip():
            lines.append(line)
    return "\n".join(lines)


def split_columns(words, page_width):
    """检测双栏排版并返回 (left_text, right_text)，单栏返回 None。

    规则：词 x0 分布的最大间隙 > 25% 页宽、且间隙位于页面 20%-80% 之间 → 双栏。
    解决教材对话页双栏交错问题（左栏第一行、右栏第一行…交错输出）。
    """
    if not words or len(words) < 10 or not page_width:
        return None
    x0s = sorted(w["x0"] for w in words)
    max_gap = 0
    split_x = None
    for a, b in zip(x0s, x0s[1:]):
        gap = b - a
        if gap > max_gap:
            max_gap = gap
            split_x = (a + b) / 2
    if max_gap < page_width * 0.25 or split_x is None:
        return None
    if not (page_width * 0.2 < split_x < page_width * 0.8):
        return None
    left = [w for w in words if w["x0"] < split_x]
    right = [w for w in words if w["x0"] >= split_x]
    if not left or not right:
        return None
    return _col_text(left), _col_text(right)


def _extract_page_text(page) -> str:
    """pdfplumber 单页提取：双栏页面按左→右阅读序（避免交错），否则默认提取。"""
    text = page.extract_text() or ""
    try:
        words = page.extract_words(x_tolerance=3)
    except Exception:  # noqa: BLE001
        words = []
    if not words:
        return text
    cols = split_columns(words, page.width or 0)
    if cols is None:
        return text
    left, right = cols
    return left + "\n" + right


def extract_pages(pdf_path):
    """逐页提取文本，返回 [page_text, ...]（索引 = 页码 - 1）。"""
    pages = []
    try:
        import pdfplumber

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                pages.append(_extract_page_text(page))
    except ImportError:
        try:
            import pypdf as pypdf_module
        except ImportError:
            import PyPDF2 as pypdf_module

        reader = pypdf_module.PdfReader(str(pdf_path))
        for page in reader.pages:
            pages.append(page.extract_text() or "")
    return pages


def has_text_layer(pdf_path) -> int:
    """粗检查 PDF 是否含文本层，返回识别到的文本操作符数量；0 = 疑似扫描版需 OCR。"""
    data = Path(pdf_path).read_bytes()
    count = 0
    for m in re.finditer(rb"stream\r?\n", data):
        chunk = data[m.end():]
        end = chunk.find(b"endstream")
        if end == -1:
            continue
        chunk = chunk[:end]
        try:
            chunk = zlib.decompress(chunk)
        except Exception:
            pass
        count += len(re.findall(rb"\)\s*Tj|\]\s*TJ", chunk))
    return count


# ---------------------------------------------------------------------------
# 关键字定位
# ---------------------------------------------------------------------------

# 单元总览页判定：一页内同时出现 >=2 个“互斥”模块标题（不含 Find the rule 等子内容，
# 否则 Talking time 正文页会因含 Talking time+Find the rule 被误判）。含变体标题。
OVERVIEW_MODULE_RE = re.compile(
    r"\b(Topic words|Fun time|Chant time|Rhyme time|Talking time|Story time|Reading time|Project)\b", re.IGNORECASE
)


def _is_overview_page(text: str) -> bool:
    """判断是否为单元总览页（目录页）。

    特征：一**行**内混排 >=2 个互斥模块标题（如 "Big task Topic words Fun time"）。
    正文页模块标题独立成行（"Topic words\nkite-flying"），即使同页含多个模块也不会误判。
    """
    for line in (text or "").splitlines():
        hits = set(m.lower() for m in OVERVIEW_MODULE_RE.findall(line))
        if len(hits) >= 2:
            return True
    return False


def find_first(pages, pattern: re.Pattern, start: int = 0):
    """返回第一个命中 pattern 的页面索引（0-based），找不到返回 None。"""
    for i in range(start, len(pages)):
        if pattern.search(pages[i]):
            return i
    return None


def locate_unit_range(pages, unit: int):
    """定位 Unit N 正文范围。

    返回 (start_idx, end_idx, warnings) 或 (None, error_msg, [])。
    - 起点 = 第一次出现 "Unit N" 的页；若该页是单元总览页（多个模块标题+摘要混排），
      自动跳过到下一页（否则总览页摘要会污染分桶，正文锚点被总览页先命中而丢失）
    - 终点 = 起点之后第一次出现 "Unit N+1" 的页（不含）；找不到取最后一页并告警
    - 起点与终点同页 = 目录页同时命中，告警
    """
    pat_start = re.compile(rf"\bUnit\s*{unit}\b", re.IGNORECASE)
    pat_end = re.compile(rf"\bUnit\s*{unit + 1}\b", re.IGNORECASE)

    start = find_first(pages, pat_start)
    if start is None:
        return None, f"未找到起点关键字 'Unit {unit}'", []

    # 跳过单元总览页（目录页，含多个模块标题+摘要）
    overview_skipped = 0
    guard = 0
    while start < len(pages) - 1 and _is_overview_page(pages[start]) and guard < 5:
        start += 1
        overview_skipped += 1
        guard += 1

    end = find_first(pages, pat_end, start=start)
    warnings = []
    if overview_skipped:
        warnings.append(f"已跳过 {overview_skipped} 页单元总览页（目录页）")
    if end is None:
        end = len(pages)
        warnings.append(f"未找到终点 'Unit {unit + 1}'，已取到最后一页")
    elif end == start:
        warnings.append("起点与终点同页（疑似目录页），结果需人工核对")

    return (start, end), None, warnings


# ---------------------------------------------------------------------------
# 机械清洗
# ---------------------------------------------------------------------------

DIGIT_LINE = re.compile(r"(?m)^[ \t]*(\d{1,3})[ \t]*$")
UNIT_HEADER_LINE = re.compile(r"(?mi)^[ \t]*unit[ \t]+\d+[ \t]*$")

TERMINAL_PUNCT = (".", "!", "?", ":", ";", "。", "！", "？")
CONTINUATION_PUNCT = (",", "-", "—", "(", '"', "'", "“", "‘")


def should_join(a: str, b: str) -> bool:
    """判断两行是否应接回一行（PDF 硬换行截断 vs 列表项/标题）。"""
    if not b:
        return False
    if a.endswith(TERMINAL_PUNCT):
        return False          # 上一行句子已完整
    if a.endswith(CONTINUATION_PUNCT):
        return True           # 以逗号/连字符结尾，明显续行
    if b[0].islower():
        return True           # 下一行小写开头，是句子延续
    return False              # 下一行大写开头 → 新标签/标题


def join_lines(lines, mode="smart"):
    if mode == "all":
        return [" ".join(l for l in lines if l)]
    if mode == "keep":
        return [l for l in lines if l]
    out = []
    buf = lines[0]
    for nxt in lines[1:]:
        if should_join(buf, nxt):
            buf = buf + " " + nxt
        else:
            out.append(buf)
            buf = nxt
    out.append(buf)
    return out


def clean_text(text: str, strip_unit_headers: bool = False, join_mode: str = "smart"):
    """机械清洗：删孤立页码/插图编号行，智能接回断行。

    返回 (cleaned_text, removed_numbers)。
    """
    removed_numbers = []
    chunks = re.split(r"\n{2,}", text)
    cleaned_chunks = []

    seen_title = {"done": False}

    def drop_header(m):
        if not seen_title["done"]:
            seen_title["done"] = True
            return m.group(0)
        return ""

    for chunk in chunks:
        for m in DIGIT_LINE.finditer(chunk):
            removed_numbers.append(int(m.group(1)))
        chunk = DIGIT_LINE.sub("", chunk)

        if strip_unit_headers:
            chunk = UNIT_HEADER_LINE.sub(drop_header, chunk)

        chunk = re.sub(r"\n+", "\n", chunk).strip()
        if not chunk:
            continue

        lines = [ln.strip() for ln in chunk.split("\n") if ln.strip()]
        if not lines:
            continue

        cleaned_chunks.append("\n".join(join_lines(lines, join_mode)))

    return "\n\n".join(cleaned_chunks), sorted(set(removed_numbers))


# ---------------------------------------------------------------------------
# 机械粗分桶
# ---------------------------------------------------------------------------

# 6 模块标题锚点：行首匹配（清洗接行后标题可能与内容同行，不能要求独立成行）。
# 兼容教材变体：Fun time 位置可能是 Chant time / Rhyme time，Story time 位置可能是 Reading time。
MODULE_ANCHOR_RE = re.compile(
    r"(?mi)^\s*(Topic words|Fun time|Chant time|Rhyme time|Talking time|Story time|Reading time|Project|Words to use)\b"
)
# 规范 key 顺序（Stage 2 预览 / Stage 3 左栏 Tab 顺序）
MODULE_KEYS = [
    "topic_words",
    "fun_time",
    "talking_time",
    "story_time",
    "project",
    "words_to_use",
]

_ANCHOR_KEY = {
    "Topic words": "topic_words",
    "Fun time": "fun_time",
    "Chant time": "fun_time",
    "Rhyme time": "fun_time",
    "Talking time": "talking_time",
    "Story time": "story_time",
    "Reading time": "story_time",
    "Project": "project",
    "Words to use": "words_to_use",
}


def bucket_modules(text: str) -> dict:
    """机械粗分桶：按模块标题锚点把清洗后文本切成 6 模块。

    只取每个 key 第一次出现的锚点；定位不到的模块为 None。
    粗分桶允许脏（精准归整交给 S5 LLM 任务）。
    """
    result = {k: None for k in MODULE_KEYS}
    matches = list(MODULE_ANCHOR_RE.finditer(text))
    for i, m in enumerate(matches):
        key = _ANCHOR_KEY.get(m.group(1))
        if key is None or result.get(key) is not None:
            continue
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        result[key] = text[start:end].strip()
    return result


# ---------------------------------------------------------------------------
# 书末词表区域定位（设计共识 §6 新算法）
# ---------------------------------------------------------------------------

WORDS_TO_USE_RE = re.compile(r"words?\s+to\s+use", re.IGNORECASE)


def locate_words_region(pages):
    """定位书末词表区域（排除前 1/4 目录页）。

    废弃 trials 的"首次→最后出现页"算法（目录页 'Topic words' 列标题会误触发）。
    新算法：从全书 1/4 处正向找第一次出现的 'Words to use' 标题页 → 该页到最后一页。
    返回 (start_idx, end_idx_exclusive) 或 None。
    """
    n = len(pages)
    if n < 4:
        return None
    skip = n // 4
    for i in range(skip, n):
        if WORDS_TO_USE_RE.search(pages[i]):
            return (i, n)
    return None


# ---------------------------------------------------------------------------
# audio_slicer 同步（S11 增强）：TTS 完成后把整段音频 + 句子切片写入
# audio_slicer（Drama=English Book (Grade 5), Season=1, Episode=Unit 数值），
# 直接复用 AudioWorkbench 的跟读/切片调整功能。
# ---------------------------------------------------------------------------

def sync_tts_to_audio_slicer(task) -> bool:
    """把任务的学习音频同步到 audio_slicer 三张表（幂等，可重复调用）。

    - SourceAudio: drama="English Book (Grade 5)", season=1, episode=task.unit, file=MP3
    - AudioChunk: chunk_index=0（整个音频 1 个 chunk）, file=同一 MP3
    - AudioSlice: 每个句子一条（start_time/end_time/original_text），先删后建

    失败返回 False（TTS 状态不受影响），成功返回 True。
    """
    import os

    from django.conf import settings
    from django.core.files import File
    from django.db.models.signals import post_save

    from audio_slicer.models import AudioChunk, AudioSlice, Drama, SourceAudio
    from audio_slicer.signals import trigger_audio_slicing

    if not task.tts_audio_url or not task.tts_timestamps:
        return False
    audio_path = os.path.join(settings.MEDIA_ROOT, task.tts_audio_url)
    if not os.path.exists(audio_path):
        logger.warning(f"[corpus] sync_tts_to_audio_slicer: 音频不存在 {audio_path}")
        return False

    drama, _ = Drama.objects.get_or_create(name="English Book (Grade 5)")
    fname = os.path.basename(audio_path)

    # 断开 SourceAudio 上传 signal（自动 60s 切块 + scripts 翻译任务）——本同步只需要
    # 整个音频 1 个 chunk（index 0），完成后恢复 signal 避免影响其它功能
    disconnected = post_save.disconnect(trigger_audio_slicing, sender=SourceAudio)
    try:
        source, _ = SourceAudio.objects.get_or_create(
            drama=drama, season=1, episode=task.unit,
            defaults={"title": task.name or f"Unit {task.unit}"},
        )
        if not source.title:
            source.title = task.name or f"Unit {task.unit}"
        with open(audio_path, "rb") as fh:
            source.file.save(fname, File(fh), save=True)

        chunk, _ = AudioChunk.objects.get_or_create(source_audio=source, chunk_index=0)
        with open(audio_path, "rb") as fh:
            chunk.file.save(fname, File(fh), save=True)
        chunk.has_slices = True
        chunk.save()
    finally:
        if disconnected:
            post_save.connect(trigger_audio_slicing, sender=SourceAudio)

    # 切片先删后建（幂等；避免 unique (chunk, start, end) 冲突）
    chunk.slices.all().delete()
    created = 0
    for mod_key in ("fun_time", "talking_time", "story_time", "project"):
        for s in (task.tts_timestamps or {}).get(mod_key, []) or []:
            start, end = s.get("start"), s.get("end")
            if start is None or end is None:
                continue
            AudioSlice.objects.create(
                audio_chunk=chunk,
                start_time=round(float(start), 2),
                end_time=round(float(end), 2),
                original_text=s.get("text", ""),
            )
            created += 1
    logger.info(f"[corpus] 已同步 {task.name} 到 audio_slicer（{created} 个切片）")
    return True
