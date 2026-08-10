"""
TTS 学习音频 + whisper 时间戳对齐（#33 S11）。

设计共识 §8：
- 学习音频 = Gemini（复用 english_corner.ai_services.generate_tts_audio，一天 10 次免费）
- 练习卷听力 = edge-tts（S9 接入）
- 流程：四模块文本整段拼接 → Gemini TTS → 本地 whisper（localhost:8001）转写拿 segments
  → 已知句子与 segments 贪心对齐 → {module: [{text, start, end}]}

真实验证留 S14（whisper 对齐精度 / quota 消耗）。
"""
import json
import logging
import os
import re
import subprocess
import time

logger = logging.getLogger(__name__)

WHISPER_BASE_URL = os.getenv("WHISPER_BASE_URL", "http://localhost:8001")

# 学习音频包含的模块（Topic words / Words to use 不生成音频，Q7 共识）
TTS_MODULE_KEYS = ["fun_time", "talking_time", "story_time", "project"]

# 各模块参与朗读的字段（排除：grammar_tip 语法点、sections 的 B/Step 子章节）
_TTS_BUILD_FIELDS = {
    "fun_time": ("title", "content", "sound"),      # Sound 拼读示例句保留（可跟读）
    "talking_time": ("title", "content"),           # 排除 Find the rule
    "story_time": ("title", "content"),
    "project": ("title", "content"),                # 范文正文，排除 B/Step 步骤
}


def build_tts_text(mods: dict) -> dict:
    """跟读专用文本分割（#33 增强）：从 cleaned_modules 提取朗读内容。

    过滤规则：
    - talking_time 的 grammar_tip（Find the rule 语法归纳）不朗读
    - project 的 sections（B blabla + Step 1/2/3 操作指导）不朗读
    - "-- " 前缀（LLM 对不可靠角色名的占位）删除——否则 whisper 对齐时
      句子带 "--" 而转写文本没有，SequenceMatcher 匹配失败导致无时间戳

    返回 {module_key: {"text": str, "sentences": [str]}}
    """
    result = {}
    for key in TTS_MODULE_KEYS:
        d = mods.get(key)
        if not isinstance(d, dict):
            continue
        parts = [d.get(f) for f in _TTS_BUILD_FIELDS[key] if d.get(f)]
        text = "\n".join(parts)
        if not text.strip():
            continue
        # 去掉 "--" 角色名占位前缀（保留句子内容，对话仍可朗读）
        cleaned_lines = []
        for ln in text.splitlines():
            stripped = re.sub(r"^\s*--\s*", "", ln).strip()
            if stripped:
                cleaned_lines.append(stripped)
        cleaned = "\n".join(cleaned_lines).strip()
        if cleaned:
            result[key] = {"text": cleaned, "sentences": split_sentences(cleaned)}
    return result


# ---------------------------------------------------------------------------
# TTS 生成（Gemini）
# ---------------------------------------------------------------------------

def generate_learning_audio(text: str, task_id: int) -> str:
    """Gemini TTS 生成整段音频。

    返回相对 media URL（如 english_corner/tts/0/{task_id}.wav）。
    复用平台 generate_tts_audio（conversation_id=0，与 reader 一致）。
    """
    from english_corner.ai_services import generate_tts_audio

    rel_url = generate_tts_audio(text, conversation_id=0, message_id=task_id)
    if not rel_url:
        raise RuntimeError("Gemini TTS 返回空（quota 用尽或调用失败）")
    return rel_url


# ---------------------------------------------------------------------------
# Whisper 转写客户端
# ---------------------------------------------------------------------------

def split_sentences(text: str) -> list:
    """按英文句号/感叹号/问号切分句子，过滤空段。"""
    sents = [s.strip() for s in SENT_SPLIT.split(text or "") if s.strip()]
    return sents


def convert_audio_to_mp3(rel_url: str) -> str:
    """WAV → MP3（ffmpeg，128kbps）。学习页播放用 MP3（seek 高效，大文件可靠）。

    返回 mp3 相对 URL；转码失败返回原 WAV URL（功能可用，仅 seek 稍慢）。
    """

    from django.conf import settings

    wav_path = os.path.join(settings.MEDIA_ROOT, rel_url)
    if not os.path.exists(wav_path):
        return rel_url
    mp3_path = wav_path.rsplit(".", 1)[0] + ".mp3"
    if os.path.exists(mp3_path):
        return os.path.relpath(mp3_path, settings.MEDIA_ROOT).replace("\\", "/")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", wav_path, "-codec:a", "libmp3lame", "-b:a", "128k", mp3_path],
            check=True, capture_output=True, timeout=180,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[corpus] WAV→MP3 转码失败（保留 WAV）: {exc}")
        return rel_url
    return os.path.relpath(mp3_path, settings.MEDIA_ROOT).replace("\\", "/")
