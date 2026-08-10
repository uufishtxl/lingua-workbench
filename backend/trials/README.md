# 教材 PDF → Unit 结构化内容 处理管线（trials 原型）

> 本文档是给新对话 LLM 的参考资料。描述了 `backend/trials/` 下 4 个脚本构成的完整管线：
> **PDF 提取指定 Unit 正文 → 提取书末 Words to use 词表 → 清理噪声 → DeepSeek 模块化分桶 → HTML 展示**。

## 0. 背景

- 源文件：`backend/english_book_5a.pdf`（小学英语五年级上册，英文课文）
- 目标：按 Unit 切出课文内容，按**固定 7 模块**结构化，供网页展示 / 后续 LLM 分析
- 运行环境：**Windows venv**（`backend/venv`，已装 `pdfplumber`、`openai`、`requests`、`python-dotenv`）；pi 容器内没有这些库，只能做语法/逻辑校验，不能真跑
- 现状：原型脚本，输出到 `backend/trials/outputs/`，尚未接入 Django 正式功能

## 1. 管线总览（数据流）

```
english_book_5a.pdf
        │ ① extract_unit.py --unit 2
        ▼
outputs/unit_2.json            （原始提取：Unit 2 正文，含页码噪声）
        │ ② extract_unit.py --words 2
        ▼
outputs/unit_2.words.json      （书末 Words to use 词表区域，未按 Unit 切分）
        │ ③ clean_unit_json.py --unit 2
        ▼
outputs/unit_2.cleaned.json    （清掉页码/插图编号，智能接回断句）
        │ ④ analyze_unit.py --unit 2   （读 .env 的 DeepSeek key）
        ▼
outputs/unit_2.analysis.json   （7 模块结构化：topic_words/fun_time/.../words_to_use）
        │ ⑤ make_viewer.py     （扫描 outputs/，合并 analysis + words）
        ▼
outputs/unit_data.js  ──<script src>──  unit_viewer.html（静态网页，双击即开）
```

## 2. 文件清单

| 文件 | 行数 | 职责 |
|---|---|---|
| `trials/extract_unit.py` | ~255 | ① PDF 提取：指定 Unit 正文（`--unit N`）或书末词表（`--words N`） |
| `trials/clean_unit_json.py` | ~179 | ③ 清理：删页码/题号、智能接行，输出 `.cleaned.json` |
| `trials/analyze_unit.py` | ~250 | ④ 调 DeepSeek 按 7 模块结构化，输出 `.analysis.json` |
| `trials/make_viewer.py` | ~458 | ⑤ 聚合所有 outputs 生成 `unit_data.js` + 静态 `unit_viewer.html` |
| `trials/outputs/` | - | 中间产物与最终数据（`unit_2.json` 等） |
| `trials/trials.py` | - | 无关的旧实验（LLM 表达查询），忽略 |

## 3. extract_unit.py —— PDF 文本提取

### 3.1 用法

```bash
python extract_unit.py --unit 2                      # 提取 Unit 2 → Unit 3 之间的正文
python extract_unit.py --words 2                     # 提取书末 'Words to use' 词表区域
python extract_unit.py --unit 2 --pdf ../english_book_5a.pdf
python extract_unit.py --unit 2 --txt                # 额外输出 .txt
python extract_unit.py --unit 2 --start-marker "..." # 自定义起点正则
```

`--unit` 与 `--words` 二选一，都不传时报错提示。

### 3.2 关键函数

- `extract_pages(pdf_path)` → `[page_text, ...]`：优先 `pdfplumber`，回退 `pypdf`/`PyPDF2`。每页 1 个元素，索引 = 页码-1
- `has_text_layer(pdf_path)` → int：zlib 解压流数 `Tj/TJ` 操作符，0 则提示"可能是扫描版需 OCR"
- `find_first(pages, pattern, start)` → 页面索引 或 None
- `extract_words_to_use(pages, unit, pdf_name)` → dict：找所有含 `words?\s+to\s+use`（忽略大小写）的页，区域 = **首次出现页 → 最后出现页**；另按 `Unit N` ~ `Unit N+1` 关键字切 `unit_block`（诊断用）

### 3.3 单元正文提取算法

1. 起点页 = 第一次出现 `\bUnit\s*N\b`（忽略大小写）
2. 终点页 = 起点之后第一次出现 `\bUnit\s*(N+1)\b`；找不到 → 取到最后一页并告警
3. 起点页从关键字处截取（去掉页眉前缀），页面间用 `\n\n` 连接
4. 输出 `outputs/unit_{N}.json`

### 3.4 JSON schema（unit_N.json）

```json
{
  "unit": 2,
  "source_pdf": "english_book_5a.pdf",
  "start_marker": "\\bUnit\\s*2\\b",
  "end_marker": "\\bUnit\\s*3\\b",
  "start_page": 23,              // 1-based，包含
  "end_page_exclusive": 31,      // 1-based，不包含
  "included_pages": [23, 24, ..., 30],
  "total_chars": 4476,
  "text": "整段正文（页间 \\n\\n 分隔）",
  "pages": [{"page": 23, "text": "该页原文"}]
}
```

### 3.5 JSON schema（unit_N.words.json）

```json
{
  "unit": 2,
  "source_pdf": "english_book_5a.pdf",
  "words_start_page": 58,
  "words_end_page_exclusive": 62,
  "included_pages": [58, 59, 60, 61],
  "text": "整个词表区域文本（未按 Unit 切分）",
  "pages": [{"page": 58, "text": "..."}],
  "unit_block": {"start_page": 59, "end_page_exclusive": 61,
                 "text": "按 Unit 2~Unit 3 关键字切出的块"}   // 可能为 null
}
```

> 设计决定：词表**整段**交给 DeepSeek 按 Unit 归类（`analyze_unit.py`），因为词表版面未知（多栏/多页），关键字切块只作参考。

### 3.6 已知限制

- **`--words` 区域算法（首次→最后出现页）未在真实书上验证**。若实际排版是"每单元末尾各一个 Words to use"或词表不连续，需要调整
- PDF 是 **CID 字体十六进制编码**（`<047908D1...>Tj`），容器里无法直接解文本，只能在 Windows 上跑
- 目录页可能同时出现 Unit N 和 Unit N+1（起止同页），会告警但需人工核对

## 4. clean_unit_json.py —— 清理

### 4.1 用法

```bash
python clean_unit_json.py --unit 2                 # → outputs/unit_2.cleaned.json
python clean_unit_json.py --unit 2 --inplace       # 直接覆盖原文件（慎用！见 4.4 坑）
python clean_unit_json.py --json xxx.json --out yyy.json
python clean_unit_json.py --strip-unit-headers     # 顺带删重复的 "Unit N" 页眉（保留第一次）
python clean_unit_json.py --join-mode smart|all|keep   # 默认 smart
```

### 4.2 清理规则（clean_text 函数，作用于 text 和每个 page.text）

1. 删除**单独成行的 1~3 位数字**（页码 17/18...、插图编号 1/2/3）：`(?m)^[ \t]*(\d{1,3})[ \t]*$`
2. 可选：删除单独成行的 "Unit N" 页眉，**保留第一次出现**（单元标题）
3. 折叠块内多余空行
4. 接行（见下）

### 4.3 接行策略（--join-mode）

PDF 把散文**硬换行**（如 `I use all my\nstrength for every action.`），要接回句子；但**导图/列表页**（如 Unit 概览页）换行本身是结构，不能全接平。

- `smart`（默认）：`should_join(a, b)` 规则——
  - a 以 `.!?:;。！？` 结尾（句子完整）→ **不接**
  - a 以 `,-—("'“‘` 结尾（明显续行）→ **接**
  - b 以小写开头（句子延续）→ **接**
  - b 以大写开头（新标签/标题）→ **不接**
- `all`：全部接成一行（旧行为）
- `keep`：保留原始换行，只删页码

### 4.4 已知坑

- **`--inplace` 曾误覆盖原始提取数据**（换行结构不可恢复）。正式功能应默认写新文件 + 保留原始
- 教材练习里的**填空占位数字**（如 `12 kinds of 1`、`stand like a 2`）是内容不是页码，规则删不掉也不能删——它们不是独立成行，所以不受影响
- 弯引号：PDF 文本用 `’`（U+2019），做字符串匹配时注意

## 5. analyze_unit.py —— DeepSeek 模块化分桶

### 5.1 用法

```bash
python analyze_unit.py --unit 2                     # 读 outputs/unit_2.cleaned.json
python analyze_unit.py --unit 2 --dry-run           # 只打印提示词，不调用 API
python analyze_unit.py --unit 2 --model deepseek-v4-pro
python analyze_unit.py --unit 2 --words-json xxx.json
```

### 5.2 环境与模型解析

- `load_dotenv(backend/.env)`，读 `DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL`（兼容旧 `BASE_URL`，缺省 `https://api.deepseek.com`）
- 模型解析 `resolve_model()`：`--model` > `DEEPSEEK_MODEL` > `LLM_MODEL_NAME`/`MODEL_NAME`（**只认含 "deepseek" 的名字**）> 默认 `deepseek-v4-flash`
- **坑**：`.env` 的 `MODEL_NAME = gemini-2.5-flash` 是给 Gemini 用的（带空格写法）。曾因此把 gemini 模型名发给 DeepSeek 收到 400。正式功能务必区分 provider 专属模型变量（现在 LLM_PROVIDER=deepseek、LLM_MODEL_NAME=deepseek-v4-flash）

### 5.3 API 调用

- 优先 `openai` 客户端（`OpenAI(api_key, base_url)`），回退 `requests` POST `{base_url}/chat/completions`
- 先带 `response_format={"type":"json_object"}`，**任何异常自动去掉重试一次**（v4-flash 可能不支持 json mode）
- `temperature=0.2`，timeout 默认 120s
- 响应解析 `parse_json_response()`：容忍 ```json 代码围栏、前后杂字，失败则提取第一个 `{...}`

### 5.4 7 模块 Schema（核心提示词，逐字保留）

模块顺序与规则：
1. `topic_words` — 生词列表，**用 " / " 分隔**
2. `fun_time` — 海报文字、活动描述 + **Sound 部分**（few-shot：`Sound ar garden` + `The game card says, "Find a star, a toy car and a bar of chocolate in the garden. It's not very hard."`）
3. `talking_time` — 对话/对白（含角色名）
4. `story_time` — 完整故事叙事（以标题开头）
5. `grammar_tip` — "Find the rule" / "Quick tip" 后的语法归纳
6. `project` — "Project"/"Big task" 下范文或步骤；**"A View and learn" 小标题不输出**；"B Introduce your favourite game" 作为子章节按 **Step 1 / 2 / 3...** 输出
7. `words_to_use` — 从词表文本中提取 Unit N 的单词，**用 " / " 分隔**；找不到返回 null

约束：
- 忽略页码（17, 18...）；忽略单独题号 "1","2","3"，但**填空占位符句子**（`I run ___`）保留
- **不抓取** "Match and tell" 及其内容
- **不抓取** "I can ..." 掌握度句子（如 `I can say the names of some traditional games.`）
- Fun/Talking/Story Time/Project 后**第一行是 Title，保留**
- 模块缺失返回 null；保留英文原文，不加解释

### 5.5 输出 schema（unit_N.analysis.json）

```json
{
  "unit": 2,
  "model": "deepseek-v4-flash",
  "source": "unit_2.cleaned.json",
  "analyzed_at": "2026-08-06 12:00:00",
  "modules": {
    "topic_words": "kite-flying / tug of war / ...",
    "fun_time": "...", "talking_time": "...", "story_time": "...",
    "grammar_tip": "...", "project": "...", "words_to_use": "..."
  },
  "raw_response": "DeepSeek 原始返回（调试用）"
}
```

- 输入超 50000 字符会截断并告警
- JSON 解析失败时 modules 为空但 raw_response 仍保存

## 6. make_viewer.py —— 聚合与静态网页

### 6.1 用法

```bash
python make_viewer.py                    # 扫描 outputs/unit_*.json（优先 .cleaned），合并全部 Unit
python make_viewer.py --unit 2           # 只含 Unit 2
python make_viewer.py --json xxx.json    # 只含指定文件
```

### 6.2 逻辑

- `collect_data()`：扫 `unit_{N}.json` / `unit_{N}.cleaned.json`（**优先 cleaned**），并合并 `unit_{N}.analysis.json` → `data["analysis"]`、`unit_{N}.words.json` → `data["words"]`
- 输出 `outputs/unit_data.js`：`window.UNIT_DATA = {...}`（`</` 转义为 `<\/`）
- 输出 `unit_viewer.html`：静态模板，通过 `<script src="outputs/unit_data.js">` 引用数据

### 6.3 网页功能

- **Unit 下拉框**切换（数据文件里所有 Unit）
- 4 个标签页：全文（页间分隔条、搜索高亮）、按页（卡片+复制本页）、**结构化**（7 模块卡片，缺失显示"（本单元无此模块）"）、原始 JSON（复制）
- 头部元信息：来源 PDF、页码范围、页数/字符数、起止关键字
- 数据内嵌于 js 文件，**双击 file:// 即可打开**（script 标签不受 CORS 限制，fetch 会）

### 6.4 模块中文名映射（HTML 端）

`topic_words=生词 · Topic Words`、`fun_time=活动 · Fun Time`、`talking_time=对话 · Talking Time`、`story_time=故事 · Story Time`、`grammar_tip=语法 · Grammar Tip`、`project=范文 · Project`、`words_to_use=词汇表 · Words to use`

## 7. 完整运行流程（Windows）

```bash
cd C:\projects\lingua-workbench\backend\trials
python extract_unit.py --unit 2          # ① 提取正文 → outputs/unit_2.json
python clean_unit_json.py --unit 2       # ③ 清理 → outputs/unit_2.cleaned.json
python extract_unit.py --words 2         # ② 词表 → outputs/unit_2.words.json
python analyze_unit.py --unit 2          # ④ DeepSeek 7 模块 → outputs/unit_2.analysis.json
python make_viewer.py                    # ⑤ 刷新 outputs/unit_data.js + unit_viewer.html
```

## 8. 已知问题 / 待验证项（给新对话 LLM 的重点）

1. **词表区域算法未在真实书验证**（`--words` 的"首次→最后出现页"假设）
2. `outputs/` 中的 `unit_2.words.json`、`unit_2.analysis.json` 是**测试 mock**，真实运行会覆盖；`unit_2.json` 曾被扁平化污染（无换行），需重跑 ①
3. `.env` 中 `MODEL_NAME` 是 Gemini 的，DeepSeek 模型名在 `LLM_MODEL_NAME`（= deepseek-v4-flash）
4. 结构化输出依赖 DeepSeek JSON 稳定性——正式化时应考虑 function calling / 重试 / 人工校验
5. 页码清理会误删插图编号行（1/2/3），对正文无影响，但 `match-and-tell` 等练习结构依赖后续 LLM 归整
6. 扫描版 PDF（无文本层）无法处理，需 OCR

## 9. 正式化建议（原型 → 正式功能）

- 提取/清理/分析三阶段应**幂等、可缓存**（原始提取结果存库/文件，避免重复解析 PDF）
- 阶段产物落 Django model（类似现有 `audio_slicer` 的 SourceAudio/AudioChunk 模式）
- DeepSeek 调用走**异步任务**（项目已有 huey），带重试与成本统计（tokens 已在脚本打印）
- 清理规则（页码/接行/页眉）做成可配置参数
- `--inplace` 类危险操作默认禁用，保留原始提取
- 词表区域提取改为可配置/自适应（多栏、跨页、重复页眉）
- 模型名与 provider 解耦，从配置中心读取
