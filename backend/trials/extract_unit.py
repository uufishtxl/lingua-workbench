#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
临时脚本：从 PDF 中按 "Unit N" 关键字切出指定范围，输出 JSON。

用法（在 Windows 的 backend/trials 下，用装了 pdfplumber 的 venv 跑）：
    python extract_unit.py --unit 2
    python extract_unit.py --unit 2 --pdf ../english_book_5a.pdf
    python extract_unit.py --unit 5 --txt              # 额外输出纯文本 .txt 便于核对
    python extract_unit.py --words 2                   # 只提取书末 'Words to use' 词表区域

规则：
    - 起点 = 第一次出现 "Unit N" 的页面（从该关键字处开始截取）
    - 终点 = 起点之后第一次出现 "Unit N+1" 的页面（不含该页）
    - 如果找不到 Unit N+1，则取到最后一页并告警
    - --words N：提取 PDF 中 'Words to use' 词表区域（首次出现页到最后出现页），
      保存为 outputs/unit_{N}.words.json，供 analyze_unit.py 使用

输出：
    outputs/unit_{N}.json / outputs/unit_{N}.words.json
"""
import argparse
import json
import re
import sys
import zlib
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_PDF = SCRIPT_DIR.parent / "english_book_5a.pdf"
DEFAULT_OUTDIR = SCRIPT_DIR / "outputs"


# ---------------------------------------------------------------------------
# PDF 文本提取
# ---------------------------------------------------------------------------
def extract_pages(pdf_path: Path):
    """逐页提取文本，返回 [page_text, ...]（1 页 1 个元素，索引即页码-1）。

    优先 pdfplumber；没有则回退 pypdf / PyPDF2。
    """
    pages = []
    try:
        import pdfplumber

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                pages.append(page.extract_text() or "")
    except ImportError:
        try:
            import pypdf as pypdf_module
        except ImportError:
            import PyPDF2 as pypdf_module

        reader = pypdf_module.PdfReader(str(pdf_path))
        for page in reader.pages:
            pages.append(page.extract_text() or "")
    return pages


def has_text_layer(pdf_path: Path) -> int:
    """粗检查 PDF 是否含文本层（能提取出文字），返回识别到的文本操作符数量。

    纯扫描版图片 PDF 返回 0，提示需要 OCR。
    """
    data = pdf_path.read_bytes()
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
def find_first(pages, pattern: re.Pattern, start: int = 0):
    """返回第一个命中的页面索引（0-based），找不到返回 None。"""
    for i in range(start, len(pages)):
        if pattern.search(pages[i]):
            return i
    return None


WORDS_TO_USE_RE = re.compile(r"words?\s+to\s+use", re.IGNORECASE)


def extract_words_to_use(pages, unit: int, pdf_name: str):
    """提取书末 'Words to use' 词表区域（首次出现页到最后出现页）。

    词表通常按 Unit 分组，但版面未知，所以整段交给 DeepSeek 归类更稳；
    同时附带按 'Unit N' ~ 'Unit N+1' 关键字切出的 unit_block 供参考。
    返回 dict，未找到词表返回 None。
    """
    word_pages = [i for i, t in enumerate(pages) if WORDS_TO_USE_RE.search(t)]
    if not word_pages:
        return None
    start = word_pages[0]
    end = word_pages[-1] + 1

    pat_s = re.compile(rf"\bUnit\s*{unit}\b", re.IGNORECASE)
    pat_e = re.compile(rf"\bUnit\s*{unit + 1}\b", re.IGNORECASE)

    unit_block = None
    s = find_first(pages[start:end], pat_s)
    if s is not None:
        e = find_first(pages[start:end], pat_e, start=s)
        if e is None:
            e = len(pages) - start
        unit_block = {
            "start_page": start + s + 1,
            "end_page_exclusive": start + e + 1,
            "text": "\n\n".join(pages[start + s: start + e]).strip(),
        }

    return {
        "unit": unit,
        "source_pdf": pdf_name,
        "words_start_page": start + 1,
        "words_end_page_exclusive": end + 1,
        "included_pages": [i + 1 for i in range(start, end)],
        "text": "\n\n".join(pages[start:end]).strip(),
        "pages": [{"page": i + 1, "text": pages[i]} for i in range(start, end)],
        "unit_block": unit_block,
    }


def main():
    parser = argparse.ArgumentParser(description="按 Unit 关键字切取 PDF 文本范围")
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF,
                        help=f"PDF 路径（默认 {DEFAULT_PDF}）")
    parser.add_argument("--unit", type=int, default=None,
                        help="Unit 编号，例如 2 表示提取 Unit 2 到 Unit 3 之间的文字（与 --words 二选一）")
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR,
                        help=f"JSON 输出目录（默认 {DEFAULT_OUTDIR}，不存在会自动创建）")
    parser.add_argument("--start-marker", default=None,
                        help="自定义起点正则（默认自动生成 Unit {unit}）")
    parser.add_argument("--end-marker", default=None,
                        help="自定义终点正则（默认自动生成 Unit {unit+1}）")
    parser.add_argument("--txt", action="store_true",
                        help="同时输出一份纯文本 .txt 方便人工核对")
    parser.add_argument("--words", type=int, default=None,
                        help="改为提取书末 'Words to use' 词表区域（--words N 指定 Unit）")
    args = parser.parse_args()

    if args.unit is None and args.words is None:
        sys.exit("请指定 --unit N（提取单元正文）或 --words N（提取书末词表）")

    pdf_path = args.pdf.resolve()
    if not pdf_path.exists():
        sys.exit(f"找不到 PDF：{pdf_path}")

    # 先提示是否扫描版
    ops = has_text_layer(pdf_path)
    if ops == 0:
        print("[警告] 该 PDF 疑似扫描版图片（未检测到文本层），pdfplumber 可能提取不到文字，需要 OCR。")

    print(f"[1/3] 正在提取 PDF 文本：{pdf_path} ...")
    pages = extract_pages(pdf_path)
    print(f"       共 {len(pages)} 页")

    if args.words is not None:
        words = extract_words_to_use(pages, args.words, pdf_path.name)
        if words is None:
            sys.exit("未在 PDF 中找到 'Words to use' 区域，请人工检查 PDF 结构。")
        args.outdir.mkdir(parents=True, exist_ok=True)
        out_json = args.outdir / f"unit_{args.words}.words.json"
        out_json.write_text(json.dumps(words, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[2/3] 已保存词表区域：{out_json}")
        print(f"      词表区域：第 {words['words_start_page']} 页 ~ 第 {words['words_end_page_exclusive'] - 1} 页，"
              f"共 {len(words['included_pages'])} 页")
        ub = words.get("unit_block")
        if ub:
            print(f"      'Unit {args.words}' 块：第 {ub['start_page']} 页 ~ 第 {ub['end_page_exclusive'] - 1} 页，"
                  f"{len(ub['text'])} 字符")
        else:
            print(f"      词表区域内未找到 'Unit {args.words}' 关键字，将把整个词表交给 DeepSeek 按 Unit 归类。")
        print("      词表预览（前 300 字）：")
        print(words["text"][:300])
        return

    unit = args.unit
    start_pattern = args.start_marker or rf"\bUnit\s*{unit}\b"
    end_pattern = args.end_marker or rf"\bUnit\s*{unit + 1}\b"
    pat_start = re.compile(start_pattern, re.IGNORECASE)
    pat_end = re.compile(end_pattern, re.IGNORECASE)

    print(f"[2/3] 定位关键字：起点 '{pat_start.pattern}'，终点 '{pat_end.pattern}'")
    start_page = find_first(pages, pat_start)
    if start_page is None:
        sys.exit(f"未找到起点关键字 'Unit {unit}'，可用 --start-marker 自定义正则。")
    end_page = find_first(pages, pat_end, start=start_page)
    if end_page is None:
        end_page = len(pages)
        print(f"[警告] 未找到终点 'Unit {unit + 1}'，将取到最后一页（共 {len(pages)} 页）。")
    elif end_page == start_page:
        print(f"[警告] 起点与终点在同一页（第 {start_page + 1} 页），"
              f"通常是目录页同时出现两个 Unit 关键字，结果可能异常，请人工核对。")

    # 起点页从关键字处开始截取，去掉页眉等前缀
    start_text = pages[start_page]
    m = pat_start.search(start_text)
    if m:
        start_text = start_text[m.start():]

    included = list(range(start_page, end_page))
    text = "\n\n".join([start_text] + [pages[i] for i in included[1:]])
    text = text.strip()

    result = {
        "unit": unit,
        "source_pdf": pdf_path.name,
        "start_marker": pat_start.pattern,
        "end_marker": pat_end.pattern,
        "start_page": start_page + 1,                          # 1-based，包含
        "end_page_exclusive": end_page + 1 if end_page < len(pages) else None,  # 1-based，不包含
        "included_pages": [i + 1 for i in included],
        "total_chars": len(text),
        "text": text,
        "pages": [
            {"page": i + 1, "text": pages[i]}
            for i in included
        ],
    }

    args.outdir.mkdir(parents=True, exist_ok=True)
    out_json = args.outdir / f"unit_{unit}.json"
    out_json.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[3/3] 已保存 JSON：{out_json}")

    if args.txt:
        out_txt = args.outdir / f"unit_{unit}.txt"
        out_txt.write_text(text, encoding="utf-8")
        print(f"       已保存文本：{out_txt}")

    print("-" * 60)
    print(f"Unit {unit} 范围：第 {result['start_page']} 页 ~ "
          f"第 {result['included_pages'][-1]} 页，共 {len(included)} 页，"
          f"{result['total_chars']} 个字符。")
    print("提取结果预览（前 300 字）：")
    print(text[:300])


if __name__ == "__main__":
    main()
