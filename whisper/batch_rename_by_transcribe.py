"""
批量重命名音频脚本
==================
遍历 audio_super_safari_1/ 下的音频文件，用 ffmpeg 截取前 N 秒，
送本地 Whisper 转录后提取页面信息，按以下范式重命名：

    sf_1_pb_p83        →  Super Safari 1, Pupil's Book, Page 83
    sf_1_ab_p12        →  Super Safari 1, Activity Book, Page 12
    sf_1_pb_p19_4_listen_and_act  →  同页不同部分（第二轮 8s 匹配）

流程（advanced 模式）：
    1. 第一轮 4s：提取页面，唯一匹配的直接记录，同页多个文件的放入待定队列
    2. 第二轮 8s：对待定队列重试，拿到完整 extra 加后缀区分
    3. 统一执行：按文件名去重，冲突的移到 duplicates/

用法:
    python batch_rename_by_transcribe.py                    # Dry-Run，4秒
    python batch_rename_by_transcribe.py --execute          # 实际重命名
    python batch_rename_by_transcribe.py --advanced         # Dry-Run，4秒+8秒两轮
    python batch_rename_by_transcribe.py --advanced --execute  # 实际重命名，两轮
    python batch_rename_by_transcribe.py --port 9000        # 指定 Whisper 端口
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

import requests

# ── 配置 ──────────────────────────────────────────────
AUDIO_DIR = Path(__file__).parent / "audio_super_safari_1"
AUDIO_EXTENSIONS = {".mp3", ".wav", ".wma", ".m4a", ".ogg", ".flac", ".aac", ".opus", ".mp4"}
WHISPER_URL_TEMPLATE = "http://localhost:{port}/transcribe"
CLIP_DURATION_DEFAULT = 4   # 默认截取前 N 秒
CLIP_DURATION_ADVANCED = 8  # advanced 模式重试截取时长
# 已符合范式：sf_数字_ 开头的文件跳过不处理
RENAMED_PATTERN = re.compile(r"^sf_\d+_", re.IGNORECASE)
# 报告输出路径
REPORT_PATH = Path(__file__).parent / "rename_report.txt"
# ─────────────────────────────────────────────────────

# 匹配 "Pupil's Book Page X" 或 "Activity Book Page X"（大小写不敏感）
# 兼容转录误差：Pupils / Pupil s / Pupils Book / Activitybook 等
# 允许 "Unit 1 XXX" 等前缀，不要求从头匹配
# 同时捕获页面编号后的额外内容（如 "4 Listen and Act"）
PATTERN = re.compile(
    r"(?P<book1>Pupil'?s?\s*(?:Book)?)[\s,]*(?:page|Page)\s*(?P<page1>\d+)(?P<extra1>.*)"
    r"|"
    r"(?P<book2>Activity\s*(?:Book)?)[\s,]*(?:page|Page)\s*(?P<page2>\d+)(?P<extra2>.*)",
    re.IGNORECASE,
)

# 书名缩写映射
BOOK_ABBR = {
    "pupil": "pb",
    "activity": "ab",
}


@dataclass
class RenameTask:
    """一个待执行的重命名任务。"""
    src: Path              # 原始文件路径
    new_stem: str          # 新文件名（不含扩展名）
    source_round: str      # 来源轮次："4s" 或 "8s"
    extra_info: str = ""   # 额外信息（用于日志）


@dataclass
class RenameResult:
    """重命名执行结果。"""
    task: RenameTask
    status: str            # "ok" / "duplicate" / "conflict_skip"
    dest_name: str         # 最终文件名
    location: str          # "原地" / "duplicates/" / "冲突，跳过"


def extract_page_info(text: str) -> tuple[str, str] | None:
    """从转录文本中提取页面信息。

    返回 (base_name, extra_text)：
      - base_name: 'sf_1_pb_p83' 格式
      - extra_text: 页面编号后的内容，如 '4 Listen and Act' 或 ''
    """
    match = PATTERN.search(text)
    if not match:
        return None

    if match.group("book1"):  # Pupil's Book 分支
        book_key = "pupil"
        page = match.group("page1")
        extra = match.group("extra1").strip()
    else:                      # Activity Book 分支
        book_key = "activity"
        page = match.group("page2")
        extra = match.group("extra2").strip()

    abbr = BOOK_ABBR[book_key]
    base_name = f"sf_1_{abbr}_p{page}"
    return base_name, extra


def build_suffix(extra_text: str) -> str | None:
    """从额外文本生成后缀。

    规则：
      - 有 karaoke → '_数字_listen_and_do_karaoke'
      - 无 karaoke → '_数字_listen_and_act'（数字 + 3 个单词）
      - extra 为空或无法解析 → None
    """
    if not extra_text:
        return None

    # 提取数字和后面的单词（跳过标点和空格）
    m = re.search(r"(\d+)[\s.,;:!?]*(.+)", extra_text)
    if not m:
        return None

    number = m.group(1)
    words_raw = m.group(2).strip()

    if not words_raw:
        return None

    # 判断是否 karaoke
    is_karaoke = "karaoke" in words_raw.lower()

    # 提取单词（只保留字母和数字，小写化）
    words = re.findall(r"[a-zA-Z0-9]+", words_raw.lower())

    if not words:
        return None

    if is_karaoke:
        # karaoke 模式：保留所有单词
        word_part = "_".join(words)
    else:
        # 非 karaoke：只取前 3 个单词
        word_part = "_".join(words[:3])

    return f"_{number}_{word_part}"


def clip_audio(audio_path: Path, duration: int) -> Path:
    """用 ffmpeg 截取音频前 N 秒，返回临时文件路径。"""
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(audio_path),
        "-t", str(duration),
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        tmp.name,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        os.unlink(tmp.name)
        raise RuntimeError(f"ffmpeg 失败:\n{result.stderr}")
    return Path(tmp.name)


def transcribe(wav_path: Path, port: int) -> str:
    """将音频文件发送到本地 Whisper 服务，返回转录文本。"""
    url = WHISPER_URL_TEMPLATE.format(port=port)
    with open(wav_path, "rb") as f:
        resp = requests.post(
            url,
            params={"skip_llm": "true", "whisper_model": "small"},
            files={"file": (wav_path.name, f, "audio/wav")},
            timeout=120,
        )
    resp.raise_for_status()
    data = resp.json()

    task_id = data.get("task_id")
    if task_id:
        return poll_task_result(task_id, port)

    return data.get("result", data.get("text", ""))


def poll_task_result(task_id: int, port: int, max_wait: int = 120) -> str:
    """轮询任务状态直到完成，返回转录文本。"""
    import time

    url = f"http://localhost:{port}/task/{task_id}"
    for _ in range(max_wait):
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        task = resp.json()
        status = task.get("status", "")
        if status == "completed":
            return task.get("result", "")
        if status == "failed":
            raise RuntimeError(f"转录任务失败: {task.get('result', '未知错误')}")
        time.sleep(1)

    raise RuntimeError(f"转录超时（{max_wait}s），task_id={task_id}")


def process_one(audio_path: Path, duration: int, port: int, debug: bool = False) -> tuple[str, str, str] | None:
    """截取 → 转录 → 提取，返回 (base_name, extra_text, transcript) 或 None。"""
    tmp_path = None
    try:
        tmp_path = clip_audio(audio_path, duration)
        transcript = transcribe(tmp_path, port)
        result = extract_page_info(transcript)
        if result:
            return result[0], result[1], transcript
        return None
    finally:
        if tmp_path and tmp_path.exists():
            os.unlink(tmp_path)


def execute_renames(tasks: list[RenameTask], dry_run: bool, advanced: bool) -> list[RenameResult]:
    """统一执行重命名任务列表。返回执行结果。"""
    results: list[RenameResult] = []
    used_names: dict[str, Path] = {}  # new_stem -> 第一个占用的 src 路径
    dup_dir = AUDIO_DIR / "duplicates"

    for task in tasks:
        new_name = f"{task.new_stem}{task.src.suffix}"

        # 检查文件系统上是否已存在
        dest_path = AUDIO_DIR / new_name
        fs_exists = dest_path.exists() and dest_path != task.src

        # 检查本轮是否已有同名任务（第一个占用的）
        already_claimed = task.new_stem in used_names and used_names[task.new_stem] != task.src

        if fs_exists or already_claimed:
            if not advanced:
                results.append(RenameResult(
                    task=task, status="conflict_skip",
                    dest_name=new_name, location="冲突，跳过"
                ))
                continue

            # advanced：移到 duplicates/
            dup_target = dup_dir / new_name
            if dup_target.exists():
                i = 2
                while True:
                    dup_target = dup_dir / f"{task.new_stem}_{i}{task.src.suffix}"
                    if not dup_target.exists():
                        break
                    i += 1

            if not dry_run:
                dup_dir.mkdir(exist_ok=True)
                task.src.rename(dup_target)

            results.append(RenameResult(
                task=task, status="duplicate",
                dest_name=dup_target.name, location="移到 duplicates/"
            ))
            continue

        # 无冲突，正常重命名
        if task.new_stem not in used_names:
            used_names[task.new_stem] = task.src

        if not dry_run:
            task.src.rename(dest_path)

        results.append(RenameResult(
            task=task, status="ok",
            dest_name=new_name, location="原地"
        ))

    return results


def write_report(unmatched: list[str], results: list[RenameResult]):
    """写入报告文件。"""
    lines = []
    lines.append(f"批量重命名报告  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)

    lines.append(f"\n未匹配页面信息的音频 ({len(unmatched)}):")
    lines.append("-" * 40)
    if unmatched:
        for f in unmatched:
            lines.append(f"  {f}")
    else:
        lines.append("  (无)")

    conflict_results = [r for r in results if r.status in ("duplicate", "conflict_skip")]
    lines.append(f"\n冲突/移到duplicates ({len(conflict_results)}):")
    lines.append("-" * 40)
    if conflict_results:
        for r in conflict_results:
            lines.append(f"  {r.task.src.name}  ->  {r.location}/{r.dest_name}")
    else:
        lines.append("  (无)")

    lines.append("\n" + "=" * 60)

    report = "\n".join(lines)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"\n📄 报告已写入: {REPORT_PATH}")
    print(report)


def main():
    parser = argparse.ArgumentParser(description="根据 Whisper 转录结果批量重命名音频文件")
    parser.add_argument("--execute", action="store_true", default=False,
                        help="实际执行重命名（默认 Dry-Run 仅打印）")
    parser.add_argument("--port", type=int, default=8000,
                        help="本地 Whisper 服务端口（默认 8000）")
    parser.add_argument("--advanced", action="store_true", default=False,
                        help="启用两轮模式：先 4 秒，同页多个文件再 8 秒区分")
    args = parser.parse_args()

    if not AUDIO_DIR.is_dir():
        print(f"❌ 目录不存在: {AUDIO_DIR}")
        sys.exit(1)

    audio_files = sorted(
        f for f in AUDIO_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS
    )

    if not audio_files:
        print(f"⚠️  {AUDIO_DIR} 下没有找到音频文件")
        sys.exit(0)

    mode = "EXECUTE" if args.execute else "DRY-RUN"
    print(f"{'=' * 60}")
    print(f"模式: {mode}")
    print(f"Advanced: {'是 (4s + 8s 两轮)' if args.advanced else '否 (仅 4s)'}")
    print(f"目录: {AUDIO_DIR}")
    print(f"文件数: {len(audio_files)}")
    print(f"Whisper 端口: {args.port}")
    print(f"{'=' * 60}\n")

    # ── 第一轮：4 秒，提取 base_name ────────────────────
    print(f"▶ 第一轮（{CLIP_DURATION_DEFAULT}s）匹配\n")

    # base_name -> [(audio_path, extra_text), ...]
    round1_results: dict[str, list[tuple[Path, str]]] = defaultdict(list)
    unmatched_files: list[str] = []
    already_done = 0
    fail_count = 0

    for audio_path in audio_files:
        if RENAMED_PATTERN.match(audio_path.stem):
            already_done += 1
            continue

        print(f"  ▶ {audio_path.name}")

        try:
            result = process_one(audio_path, CLIP_DURATION_DEFAULT, args.port)
        except Exception as e:
            print(f"    ❌ 错误: {e}")
            fail_count += 1
            continue

        if not result:
            print(f"    ⏭ 未匹配")
            unmatched_files.append(audio_path.name)
            continue

        base_name, extra, transcript = result
        round1_results[base_name].append((audio_path, extra))
        print(f"    📌 匹配: {base_name}")

    # ── 分流：唯一匹配 → 直接记录，同页多个 或 磁盘已有同页 → 第二轮 ────
    tasks: list[RenameTask] = []
    retry_queue: list[tuple[Path, str]] = []  # (audio_path, base_name)

    for base_name, items in round1_results.items():
        # 检查磁盘上是否已有同页范式文件（如 sf_1_pb_p42.wma）
        existing_on_disk = any(
            f.is_file() and RENAMED_PATTERN.match(f.stem) and f.stem == base_name
            for f in AUDIO_DIR.iterdir()
        )

        if len(items) == 1 and not existing_on_disk:
            # 唯一匹配且磁盘上无同页文件，直接用 base_name
            audio_path, extra = items[0]
            tasks.append(RenameTask(
                src=audio_path, new_stem=base_name,
                source_round="4s", extra_info=extra
            ))
        else:
            # 同页多个文件 或 磁盘已有同页文件，放入第二轮队列
            reason = f"磁盘已有 {base_name}" if existing_on_disk else f"本批次有 {len(items)} 个"
            print(f"    ⚡ {base_name}：{reason}，需第二轮区分")
            for audio_path, extra in items:
                retry_queue.append((audio_path, base_name))

    # ── 第二轮：8 秒，对待定队列重试 ──────────────────
    if args.advanced and retry_queue:
        print(f"\n▶ 第二轮（{CLIP_DURATION_ADVANCED}s）区分 {len(retry_queue)} 个同页文件\n")

        for audio_path, base_name in retry_queue:
            print(f"  ▶ {audio_path.name}  (属于 {base_name})")

            try:
                result = process_one(audio_path, CLIP_DURATION_ADVANCED, args.port)
            except Exception as e:
                print(f"    ❌ 错误: {e}")
                fail_count += 1
                continue

            if not result:
                # 8 秒也没匹配到，降级用 base_name（可能冲突进 duplicates）
                print(f"    ⏭ 仍未匹配，使用基础名称 {base_name}")
                tasks.append(RenameTask(
                    src=audio_path, new_stem=base_name,
                    source_round="8s", extra_info=""
                ))
                continue

            _base, extra, transcript = result
            print(f"    📝 转录: {transcript!r}")
            suffix = build_suffix(extra)

            if suffix:
                final_stem = f"{base_name}{suffix}"
                print(f"    🎵 {extra!r}  ->  {final_stem}")
            else:
                final_stem = base_name
                print(f"    📌 无额外内容，使用 {final_stem}")

            tasks.append(RenameTask(
                src=audio_path, new_stem=final_stem,
                source_round="8s", extra_info=extra
            ))

    elif retry_queue and not args.advanced:
        # 没开 advanced，同页多个文件直接用 base_name（可能冲突）
        print(f"\n⚡ 有 {len(retry_queue)} 个同页文件，未开 advanced 模式，可能冲突")
        for audio_path, base_name in retry_queue:
            tasks.append(RenameTask(
                src=audio_path, new_stem=base_name,
                source_round="4s", extra_info=""
            ))

    # ── 统一执行阶段 ──────────────────────────────────
    print(f"\n▶ 执行重命名（共 {len(tasks)} 个任务）\n")

    results = execute_renames(tasks, dry_run=not args.execute, advanced=args.advanced)

    success_count = 0
    for r in results:
        if r.status == "ok":
            tag = " (Dry-Run)" if not args.execute else ""
            print(f"  ✅ {r.task.src.name}  ->  {r.dest_name}  [{r.location}]{tag}")
            success_count += 1
        elif r.status == "duplicate":
            tag = " (Dry-Run)" if not args.execute else ""
            print(f"  🔀 {r.task.src.name}  ->  {r.dest_name}  [{r.location}]{tag}")
            success_count += 1
        else:  # conflict_skip
            print(f"  ⚠️  {r.task.src.name}  ->  {r.dest_name}  [{r.location}]")

    # ── 汇总 ──────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print(f"完成！成功: {success_count}  已符合范式(跳过): {already_done}  未匹配: {len(unmatched_files)}  失败: {fail_count}")
    if not args.execute and success_count > 0:
        print(f"\n💡 以上为 Dry-Run 预览，确认无误后加 --execute 执行实际重命名。")
    elif args.execute and success_count > 0:
        print(f"\n💡 已实际执行重命名。")
    print(f"{'=' * 60}")

    # ── 写报告 ────────────────────────────────────────
    write_report(unmatched_files, results)


if __name__ == "__main__":
    main()
