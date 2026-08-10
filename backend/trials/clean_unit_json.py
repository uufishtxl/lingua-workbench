#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
临时脚本：清理 outputs/unit_{N}.json 提取文本中的页码等噪音。

处理步骤（作用于 data["text"] 和 data["pages"][].text）：
  1. 删除单独成行的数字（页码 17/18/...、插图编号 1/2/3）
  2. 折叠多余空行
  3. 把段内被换行截断的行用空格接回（保留页面间的空行作为段落分隔）
  4. （可选）删除单独成行的 "Unit N" 页眉，保留第一次出现的作为单元标题

用法（在 backend/trials 下）：
    python clean_unit_json.py --unit 2                 # → outputs/unit_2.cleaned.json
    python clean_unit_json.py --unit 2 --inplace       # 直接覆盖原文件
    python clean_unit_json.py --json xxx.json --out yyy.json
    python clean_unit_json.py --strip-unit-headers     # 顺带去掉 "Unit N" 页眉
    python clean_unit_json.py --join-mode all          # 全部接成一行(旧行为)
    python clean_unit_json.py --join-mode keep         # 保留原始换行(只删页码)
    python clean_unit_json.py --join-mode smart        # 默认：智能接回断句，保留标签/标题换行
"""
import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = SCRIPT_DIR / "outputs"

# 单独成行的数字（页码 / 插图编号）——每页 1~3 位数字
DIGIT_LINE = re.compile(r"(?m)^[ \t]*(\d{1,3})[ \t]*$")
# 单独成行的 "Unit N"（页眉/标题）
UNIT_HEADER_LINE = re.compile(r"(?mi)^[ \t]*unit[ \t]+\d+[ \t]*$")


TERMINAL_PUNCT = (".", "!", "?", ":", ";", "。", "！", "？")
CONTINUATION_PUNCT = (",", "-", "—", "(", '"', "'", "“", "‘")


def should_join(a: str, b: str) -> bool:
    """判断两行是否应接成一行：PDF 硬换行截断 vs 列表项/标题。"""
    if not b:
        return False
    if a.endswith(TERMINAL_PUNCT):
        return False          # 上一行句子已完整（以 .!?: 结尾）
    if a.endswith(CONTINUATION_PUNCT):
        return True           # 以逗号/连字符结尾，明显是续行
    if b[0].islower():
        return True           # 下一行小写开头，是句子延续
    return False              # 下一行大写开头 → 新标签/标题，保留换行


def join_lines(lines, mode):
    if mode == "all":
        return [" ".join(l for l in lines if l)]
    if mode == "keep":
        return [l for l in lines if l]
    # smart：仅接回明显被截断的续行，保留列表/标题结构
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
    """返回 (cleaned_text, removed_numbers)。"""
    removed_numbers = []

    # 先按原有页面边界（空行分隔）分块，避免“删除数字后产生的空行”被误当成页面边界
    chunks = re.split(r"\n{2,}", text)
    cleaned_chunks = []

    seen_title = {"done": False}

    def drop_header(m):
        if not seen_title["done"]:
            seen_title["done"] = True
            return m.group(0)
        return ""

    for chunk in chunks:
        # 1. 删除单独成行的数字（页码 / 插图编号）
        for m in DIGIT_LINE.finditer(chunk):
            removed_numbers.append(int(m.group(1)))
        chunk = DIGIT_LINE.sub("", chunk)

        # 2. （可选）删除重复的 "Unit N" 页眉，保留第一次出现的作为单元标题
        if strip_unit_headers:
            chunk = UNIT_HEADER_LINE.sub(drop_header, chunk)

        # 3. 折叠块内多余空行
        chunk = re.sub(r"\n+", "\n", chunk).strip()
        if not chunk:
            continue

        lines = [ln.strip() for ln in chunk.split("\n") if ln.strip()]
        if not lines:
            continue

        # 4. 按模式接回被截断的行
        cleaned_chunks.append("\n".join(join_lines(lines, join_mode)))

    return "\n\n".join(cleaned_chunks), sorted(set(removed_numbers))


def main():
    parser = argparse.ArgumentParser(description="清理 Unit 提取 JSON 中的页码噪音")
    parser.add_argument("--unit", type=int, default=None, help="Unit 编号（默认读 outputs/unit_{unit}.json）")
    parser.add_argument("--json", type=Path, default=None, help="直接指定输入 JSON（优先于 --unit）")
    parser.add_argument("--out", type=Path, default=None, help="输出路径（默认 outputs/unit_{unit}.cleaned.json）")
    parser.add_argument("--inplace", action="store_true", help="直接覆盖输入文件")
    parser.add_argument("--strip-unit-headers", action="store_true",
                        help="同时删除单独成行的 'Unit N' 页眉（保留第一次出现）")
    parser.add_argument("--join-mode", choices=["smart", "all", "keep"], default="smart",
                        help="接行策略：smart=智能接回断句(默认)，all=全部接成一行(旧行为)，keep=保留原始换行")
    args = parser.parse_args()

    if args.json:
        in_path = args.json.resolve()
    elif args.unit is not None:
        in_path = OUTPUTS_DIR / f"unit_{args.unit}.json"
    else:
        sys.exit("请指定 --unit N 或 --json 路径")

    if not in_path.exists():
        sys.exit(f"找不到输入文件：{in_path}")

    data = json.loads(in_path.read_text(encoding="utf-8"))
    raw = data.get("text", "")
    if not raw:
        sys.exit("JSON 中没有 text 字段，没什么可清理的。")

    cleaned, removed = clean_text(raw, args.strip_unit_headers, args.join_mode)

    data["text"] = cleaned
    data["total_chars"] = len(cleaned)

    # 同步清理逐页文本（查看器直接渲染 pages）
    pages_cleaned = 0
    for page in data.get("pages", []):
        raw_page = page.get("text", "")
        if not raw_page:
            continue
        cleaned_page, _ = clean_text(raw_page, args.strip_unit_headers, args.join_mode)
        if cleaned_page != raw_page:
            pages_cleaned += 1
        page["text"] = cleaned_page

    if args.inplace:
        out_path = in_path
    elif args.out:
        out_path = args.out.resolve()
    else:
        unit = data.get("unit") or args.unit
        out_path = OUTPUTS_DIR / f"unit_{unit}.cleaned.json"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"输入：{in_path}")
    print(f"输出：{out_path}")
    print(f"字符数：{len(raw)} → {len(cleaned)}（减少 {len(raw) - len(cleaned)}）")
    print(f"移除的独立数字行（页码/插图编号）：{removed}")
    print(f"已同步清理逐页文本（pages）共 {pages_cleaned} 页")
    if args.strip_unit_headers:
        print("已删除重复的 'Unit N' 页眉（保留第一次作为单元标题）")
    print("-" * 60)
    print("清理后预览（前 400 字）：")
    print(cleaned[:400])


if __name__ == "__main__":
    main()
