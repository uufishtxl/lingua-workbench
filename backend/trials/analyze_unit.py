#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
临时脚本：调用 DeepSeek，把清理后的 Unit 文本按固定 6 模块结构化（供 HTML 展示）。

用法（在 backend/trials 下，Windows venv 里运行）：
    python analyze_unit.py --unit 2                    # 读 outputs/unit_2.cleaned.json
    python analyze_unit.py --unit 2 --json xxx.json    # 指定输入文件
    python analyze_unit.py --unit 2 --dry-run          # 只打印提示词，不调用 API

词表（可选）：运行 python extract_unit.py --words 2 生成 outputs/unit_2.words.json 后，
本脚本会自动读取并让 DeepSeek 按 Unit 归到 words_to_use 模块。

读取 ../.env（backend/.env）中的 DEEPSEEK_API_KEY / DEEPSEEK_BASE_URL。
模型名解析优先级：--model > DEEPSEEK_MODEL > LLM_MODEL_NAME/MODEL_NAME（只认含 deepseek 的名字）
> deepseek-v4-flash。注意 .env 的 MODEL_NAME 可能是给其他提供商（如 Gemini）用的，不会被误用。

输出：
    outputs/unit_2.analysis.json
之后运行 python make_viewer.py，分析结果会并入 outputs/unit_data.js，
网页新增「结构化」标签展示 6 个模块。
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = SCRIPT_DIR / "outputs"
ENV_PATH = SCRIPT_DIR.parent / ".env"  # backend/.env

MODULES = ["topic_words", "fun_time", "talking_time", "story_time", "grammar_tip", "project", "words_to_use"]

SCHEMA_PROMPT = """# 任务
请将以下从 PDF 提取的 Unit {unit} 原始文本，严格按照规定的 7 个模块进行分类归整。

# 固定的模块顺序（Schema）
1. topic_words: 提取所有作为生词列表的词汇（通常是一行或两行用逗号隔开的单词），多个单词之间用 " / " 分隔。
2. fun_time: 提取海报文字、活动描述，以及 Sound 部分。Sound 部分保留原格式，参考示例：
   Sound ar garden
   The game card says, "Find a star, a toy car and a bar of chocolate in the garden. It's not very hard."
3. talking_time: 提取主要的对话/对白部分（通常包含角色名，如 "Mr Zhong, is this..."）。
4. story_time: 提取完整的故事叙事部分（通常以故事标题开头，包含情节发展）。
5. grammar_tip: 提取 "Find the rule" 或 "Quick tip" 后面的语法归纳内容。
6. project: 提取 "Project" 或 "Big task" 下的范文或步骤指南。"A View and learn" 只是引入范文的小标题，不要输出；"B Introduce your favourite game" 作为范文中的子章节出现，其内容按 Step 1 / Step 2 / Step 3... 分步骤输出。
7. words_to_use: 根据下方 "Words to use 单词表" 文本，提取 Unit {unit} 对应的单词列表，多个单词之间用 " / " 分隔；找不到则返回 null。

# 约束条件
- 忽略页码（如 17, 18, 19）。
- 忽略单独的 "1", "2", "3" 等题号标记，但如果它们属于填空占位符（如 "I run ___"），请保留该句子。
- 不抓取 "Match and tell" 及其内容。
- 不抓取 "I can ..." 这类表示学习者是否掌握某知识点的句子（如 "I can say the names of some traditional games."）。
- Fun Time / Talking Time / Story Time / Project 后出现的第一行是该模块的标题（Title），请保留标题。
- 如果某个模块在文本中没有出现，请返回 null。
- 请保留英文原文，不要添加你自己的解释。

# 输入文本
{text}

# Words to use 单词表
{words_text}

# 输出格式
请直接返回 JSON 对象，键名为上述 7 个模块名，值为对应的文本字符串或 null。"""


def load_env():
    if HAS_DOTENV:
        load_dotenv(ENV_PATH)
    else:
        print("[提示] 未安装 python-dotenv，跳过 .env 加载（仅使用系统环境变量）")
    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL") or os.getenv("BASE_URL") or "https://api.deepseek.com"
    if not api_key:
        sys.exit(f".env 中未找到 DEEPSEEK_API_KEY（查找路径：{ENV_PATH}）")
    return api_key, base_url.rstrip("/")


def resolve_model(cli_model=None):
    """模型名解析：--model > DEEPSEEK_MODEL > LLM_MODEL_NAME/MODEL_NAME(含 deepseek) > deepseek-v4-flash。

    注意：.env 里的 MODEL_NAME 可能是给其他提供商（如 Gemini）用的
    （如 gemini-2.5-flash），不能直接发给 DeepSeek，所以只认含 deepseek 的名字。
    """
    if cli_model:
        return cli_model
    for key in ("DEEPSEEK_MODEL", "LLM_MODEL_NAME", "MODEL_NAME"):
        v = os.getenv(key)
        if v and "deepseek" in v.lower():
            return v
    return "deepseek-v4-flash"


def parse_json_response(content: str) -> dict:
    """解析模型返回内容（容忍 ```json 代码围栏 / 前后多余文字）。"""
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            return json.loads(m.group(0))
        raise


def call_deepseek(api_key, base_url, model, prompt, timeout=120):
    """优先 openai 客户端，回退 requests。"""
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        kwargs = dict(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that only outputs valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        try:
            resp = client.chat.completions.create(**kwargs, response_format={"type": "json_object"})
        except Exception:
            resp = client.chat.completions.create(**kwargs)  # 模型不支持 json_object 时重试
        content = resp.choices[0].message.content
        usage = getattr(resp, "usage", None)
        return content, usage
    except ImportError:
        import requests

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that only outputs valid JSON."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        resp = requests.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"], data.get("usage")


def main():
    parser = argparse.ArgumentParser(description="DeepSeek 结构化 Unit 文本为 6 模块")
    parser.add_argument("--unit", type=int, required=True, help="Unit 编号")
    parser.add_argument("--json", type=Path, default=None, help="输入 JSON（默认 outputs/unit_{unit}.cleaned.json）")
    parser.add_argument("--out", type=Path, default=None, help="输出路径（默认 outputs/unit_{unit}.analysis.json）")
    parser.add_argument("--words-json", type=Path, default=None,
                        help="Words to use 词表 JSON（默认 outputs/unit_{unit}.words.json）")
    parser.add_argument("--dry-run", action="store_true", help="只打印提示词，不调用 API")
    parser.add_argument("--model", default=None,
                        help="模型名（默认按 DEEPSEEK_MODEL > LLM_MODEL_NAME > MODEL_NAME，只认含 deepseek 的）")
    parser.add_argument("--timeout", type=int, default=120, help="API 超时秒数（默认 120）")
    args = parser.parse_args()

    api_key, base_url = load_env()
    model = resolve_model(args.model)

    in_path = args.json or OUTPUTS_DIR / f"unit_{args.unit}.cleaned.json"
    in_path = in_path.resolve()
    if not in_path.exists():
        fallback = OUTPUTS_DIR / f"unit_{args.unit}.json"
        if fallback.exists():
            in_path = fallback
        else:
            sys.exit(f"找不到输入文件：{in_path}\n请先运行 extract_unit.py --unit {args.unit}")

    data = json.loads(in_path.read_text(encoding="utf-8"))
    text = (data.get("text") or "").strip()
    if not text:
        sys.exit("输入 JSON 中没有 text 字段。")
    if len(text) > 50000:
        print(f"[警告] 文本过长（{len(text)} 字符），已截断到 50000 字符")
        text = text[:50000]

    # ---- Words to use 词表（可选） ----
    words_path = args.words_json or OUTPUTS_DIR / f"unit_{args.unit}.words.json"
    words_text = ""
    if words_path.exists():
        words_data = json.loads(words_path.read_text(encoding="utf-8"))
        words_text = (words_data.get("text") or "").strip()
        if not words_text:
            print(f"[警告] {words_path.name} 的 text 为空")
    elif args.words_json is None:
        print(f"[提示] 未找到 {words_path.name}，words_to_use 将返回 null。"
              f"可先运行 python extract_unit.py --words {args.unit}")
    if not words_text:
        words_text = "（无）"

    prompt = SCHEMA_PROMPT.format(unit=args.unit, text=text, words_text=words_text)

    if args.dry_run:
        print(prompt)
        return

    print(f"[1/3] 输入：{in_path}（{len(text)} 字符）")
    print(f"[2/3] 调用 DeepSeek：model={model}，base_url={base_url} ...")
    t0 = time.time()
    content, usage = call_deepseek(api_key, base_url, model, prompt, timeout=args.timeout)
    elapsed = time.time() - t0

    modules = {}
    try:
        parsed = parse_json_response(content)
        modules = {k: parsed.get(k) for k in MODULES}
    except Exception as e:
        print(f"[警告] JSON 解析失败：{e}，保存原始返回供人工检查")

    out_path = (args.out or OUTPUTS_DIR / f"unit_{args.unit}.analysis.json").resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "unit": args.unit,
        "model": model,
        "source": in_path.name,
        "analyzed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "modules": modules,
        "raw_response": content,
    }
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[3/3] 已保存：{out_path}（耗时 {elapsed:.1f}s）")
    if usage:
        print(f"      tokens：{getattr(usage, 'prompt_tokens', '?')} 输入 / "
              f"{getattr(usage, 'completion_tokens', '?')} 输出")
    present = [k for k, v in modules.items() if v not in (None, "")]
    print(f"      提取到的模块（{len(present)}/{len(MODULES)}）：{', '.join(present) or '无'}")
    print("接下来运行 python make_viewer.py 刷新网页数据。")


if __name__ == "__main__":
    main()
