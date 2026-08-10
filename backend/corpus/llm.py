"""
LLM 归整（#27）：DeepSeek 把机械粗分桶文本归整为精准 6 模块。

复用平台 get_llm（ai_analysis.services，feature=default → deepseek-v4-flash）。
提示词改编自 trials/analyze_unit.py 的 SCHEMA_PROMPT，模块从 7 减为 6
（grammar_tip 并入 talking_time 的 Find the rule 子内容，见设计共识 §1.3）。
"""
import json
import logging
import re

logger = logging.getLogger(__name__)

MODULE_KEYS = [
    "topic_words",
    "fun_time",
    "talking_time",
    "story_time",
    "project",
    "words_to_use",
]

MAX_INPUT_CHARS = 50000

BUCKET_PROMPT = """# 任务
请将以下从 PDF 提取的 Unit {unit} 文本，按照规定的 6 个模块归整，识别标题/子标题/语法点/步骤，输出**结构化 JSON**。

# 模块（Schema）与输出格式
输出为 JSON 对象，键为 6 个模块名，值为以下结构（字段可省略；模块缺失时值为 null）：

1. topic_words / words_to_use:
   {{"title": "模块标题", "items": ["kite-flying", "tug of war"]}}  // items 为单词/短语列表，每项一个，不包含分隔符与中文释义
2. fun_time: 活动/歌谣类模块（教材标题可能是 **Fun time / Chant time / Rhyme time** 之一）：
   {{"title": "模块标题（用教材原标题，如 Welcome to our garden party!）", "content": "海报/活动/歌谣正文", "sound": "Sound 子内容（含 Sound ar garden 及示例句）"}}
3. talking_time:
   {{"title": "对话标题（必须保留，如 A visit to the botanical gardens）", "content": "对话/对白正文（含角色名）", "grammar_tip": "Find the rule / Quick tip 的语法归纳内容（只放语法，不放对话）"}}
   - **title 必须从原文保留对话标题**（如 "A visit to the botanical gardens"），不要遗漏。
   - 对话可能包含**多组**（双栏/多栏排版导致）：按内容流畅性分组，组与组之间用空行分隔。
   - **对话行不标注说话人**：直接写对白内容本身（如 "Slow down!"），**不要使用任何 "--" 占位符或角色名前缀**；角色名仅在原文明确标出时才保留在文本中。
   - 不得遗漏任何对话句（如 "The wall is covered with plants."），保持句子完整、顺序自然。
4. story_time: 故事/阅读类模块（教材标题可能是 **Story time / Reading time** 之一）：
   {{"title": "故事标题（如 The dragon dance）", "content": "故事叙事正文"}}
5. project:
   {{"title": "Project 标题（如 A presentation of my favourite traditional game）",
     "content": "范文正文（如 'A View and learn' 之下的内容：Kite-flying is my favourite traditional game. ...）",
     "sections": [{{"title": "子章节标题（如 B Introduce your favourite game）",
                    "steps": [{{"title": "Step 1", "content": "该步内容"}}]}}]}}

# 各模块归整细则（重要）
- topic_words: 只从 "Topic words" 标题下的生词列表提取，放入 items；不要把书末词表的内容并进来。
  **即使与 words_to_use 重复也保留；正文中有生词列表就必须输出 items，不能返回 null。**
- words_to_use: **必须**从 "# Words to use 词表" 文本中提取 Unit {unit} 的单词放入 items（即使与 topic_words 重复也保留）；
  单词与 topic_words 重复属正常；每项只保留英文单词/短语（去掉 n. / adj. 等词性标记与中文释义）；
  找不到 Unit {unit} 的词才返回 null。
- story_time: content 必须**保留原文的换行与段落结构**，禁止合并成一个大段落；
  对话按行保留（如 "Head of the dragon, slow down!" 独占一行）、叙述段落之间保留空行。
- project: content 放范文正文（"A View and learn" 只是小标题，跳过标题本身但**保留其下的范文正文**）；
  "B Introduce your favourite game" 等子章节放入 sections。

# 约束
- 忽略页码（如 17, 18, 19）与单独的题号 "1", "2", "3"；填空占位符句子（如 "I run ___"）保留。
- 不抓取练习子章节及其内容：如 "A Listen, read and circle"、"A Read and write"、"B Match and tell"、"B Discuss the questions"、"C Show and tell" 等（标题含 A/B/C + 动词开头均为练习，跳过）。
- 不抓取 "I can ..." 这类学习者掌握度句子（如 "I can say the names of some traditional games."）。
- topic_words / words_to_use 的 items 只保留生词本身，不包含其后的听力/练习内容。
- 步骤 title 为 "Step 1" / "Step 2" 格式，content 为该步指引。
- 模块在文本中缺失时返回 null。
- 保留英文原文（含换行），不要添加解释。

# 输入文本
{text}

# Words to use 词表
{words_text}

# 输出格式
直接返回 JSON 对象，键名为上述 6 个模块名，值为对应结构或 null。"""


def parse_json_response(content: str) -> dict:
    """容错解析：容忍 ```json 代码围栏 / 前后杂字；失败提取第一个 {...}。"""
    text = (content or "").strip()
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


KP_SUMMARY_PROMPT = """# 任务
请用**中文**写一段简洁的梗概（80-150 字），概括以下英语故事的故事情节。

# 故事
{story}

# 要求
- 用中文，条理清晰，适合小学教师快速核对故事内容
- 包含主要人物、事件起因/经过/结果
- 不要翻译全文，只要梗概
直接输出梗概文本，不要 JSON，不要额外解释。"""


def generate_kp_summary(story: str) -> str:
    """LLM 生成故事中文梗概（KP 预填用）。失败返回空串（不阻塞 KP 生成）。"""
    from ai_analysis.services import get_llm

    prompt = KP_SUMMARY_PROMPT.format(story=story[:8000])
    try:
        llm = get_llm(feature="default", temperature=0.3)
        return (llm.invoke(prompt).content or "").strip()
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[corpus] KP 梗概生成失败: {exc}")
        return ""


def bucket_modules_with_llm(text: str, words_text: str, unit: int) -> dict:
    """调用 DeepSeek 归整 6 模块。返回 {module_key: str|None}。

    两次尝试：先带 response_format=json_object，失败（invoke 异常或 JSON 解析失败）
    自动去掉重试一次（trials 同款兜底，v4-flash 可能不支持 json mode）。
    最终失败抛诊断错误（含原始返回内容前 200 字符）。
    """
    from ai_analysis.services import get_llm

    prompt = BUCKET_PROMPT.format(unit=unit, text=text, words_text=words_text)

    def _invoke(with_json_mode: bool):
        kwargs = dict(feature="default", temperature=0.2)
        if with_json_mode:
            kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}
        llm = get_llm(**kwargs)
        return llm.invoke(prompt).content

    last_content = None
    for attempt, with_json_mode in enumerate((True, False)):
        try:
            content = _invoke(with_json_mode)
            last_content = content
            return parse_json_response(content)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[corpus] LLM 归整第 {attempt + 1} 次尝试失败 (json_mode={with_json_mode}): {exc}")

    raise RuntimeError(
        f"LLM 归整连续失败，最后一次返回内容为空或非法 JSON: {str(last_content)[:200]!r}"
    )


# ===========================================================================
# S7 AI 修复 / 重新生成（#29）：单模块 / 单板块局部重算 + 用户指令
# ===========================================================================

FIX_MODULE_PROMPT = """# 任务
请根据用户指令，修复/重新归整以下英语教材单元的一个模块，输出**结构化 JSON**。

# 模块：{module_label}
修复后该模块必须符合以下结构（字段可省略）：
{module_schema}

# 当前模块内容
{module_text}

# 用户指令
{instruction}

# 约束
- 保留英文原文；不改变不属于指令范围的内容（只修用户要求的局部问题）。
- 缺失才返回 null；不要凭空添加原文没有的内容。
- 直接返回 JSON 对象，不要解释。"""

_MODULE_SCHEMAS = {
    "topic_words": '{{"title": "模块标题", "items": ["单词1", "单词2"]}}',
    "fun_time": '{{"title": "活动标题", "content": "正文", "sound": "Sound 子内容"}}',
    "talking_time": '{{"title": "对话标题", "content": "对话正文", "grammar_tip": "语法归纳"}}',
    "story_time": '{{"title": "故事标题", "content": "故事正文（保留换行）"}}',
    "project": '{{"title": "Project 标题", "content": "范文正文", "sections": [{{"title": "子章节", "steps": [{{"title": "Step 1", "content": "内容"}}]}}]}}',
    "words_to_use": '{{"title": "模块标题", "items": ["单词1", "单词2"]}}',
}

_MODULE_LABELS = {
    "topic_words": "Topic Words（生词列表）",
    "fun_time": "Fun time（活动/歌谣，含 Sound）",
    "talking_time": "Talking time（对话，含语法点）",
    "story_time": "Story time（故事/阅读）",
    "project": "Project（范文 + 步骤）",
    "words_to_use": "Words to use（词表）",
}


def fix_module_with_llm(module_key: str, module_text: str, instruction: str, unit: int) -> dict:
    """单模块局部修复（LLM 重算），返回结构化模块 dict。"""
    from ai_analysis.services import get_llm

    if module_key not in _MODULE_SCHEMAS:
        raise ValueError(f"未知模块: {module_key}")
    prompt = FIX_MODULE_PROMPT.format(
        module_label=_MODULE_LABELS[module_key],
        module_schema=_MODULE_SCHEMAS[module_key],
        module_text=module_text[:12000] or "（空）",
        instruction=instruction or "按模块规则重新归整（保持原有内容，修复明显错误）",
    )

    def _invoke(with_json_mode: bool):
        kwargs = dict(feature="default", temperature=0.2)
        if with_json_mode:
            kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}
        return get_llm(**kwargs).invoke(prompt).content

    last_content = None
    parsed = None
    for with_json_mode in (True, False):
        try:
            last_content = _invoke(with_json_mode)
            parsed = parse_json_response(last_content)
            break
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[corpus] fix_module 尝试失败 (json_mode={with_json_mode}): {exc}")
    if parsed is None:
        raise RuntimeError(f"AI 修复连续失败，最后返回: {str(last_content)[:200]!r}")
    return {k: parsed.get(k) for k in ("title", "content", "items", "sound", "grammar_tip", "sections")}


REGENERATE_KP_PROMPT = """# 任务
请根据用户指令，重新生成英语教材单元的一个知识点板块，直接输出文本（不要 JSON）。

# 知识点：{kp_label}
{definition}

# 相关教材内容（供提取/参考）
{context}

# 当前板块内容
{current}

# 用户指令
{instruction}

# 约束
- 与教材内容一致，不凭空编造。
- 直接输出板块文本，不要解释。"""

_KP_DEFINITIONS = {
    "vocabulary": (
        "本单元核心词汇（Topic Words 与 Words to use 合并，去重）。"
        "格式要求：每个**单词**输出 `单词 /IPA/ 中文释义`，中文释义 6 字以内，"
        "如 `roots /ruːts/ 根`；**短语**（含空格，如 tug of war）不标音标，原样保留。"
    ),
    "phrases": "本单元出现的重点短语（固定搭配）。",
    "sentence_patterns": "本单元重点句型。",
    "grammar": "本单元语法点（Find the rule / Quick tip 归纳）。",
    "phonics": "本单元自然拼读（Sound 中的字母/组合发音）。",
    "summary": "本单元故事的**中文梗概**（80-150 字）。",
    "big_task": "本单元 Big Task 范文（Project 范文正文）。",
}

_KP_LABELS = {
    "vocabulary": "词汇", "phrases": "短语", "sentence_patterns": "句型",
    "grammar": "语法", "phonics": "拼读", "summary": "梗概", "big_task": "Big Task 范文",
}

# KP 相关的模块上下文来源
_KP_CONTEXT_KEYS = {
    "vocabulary": ["topic_words", "words_to_use"],
    "phrases": ["talking_time", "story_time", "fun_time"],
    "sentence_patterns": ["talking_time", "story_time"],
    "grammar": ["talking_time"],
    "phonics": ["fun_time"],
    "summary": ["story_time"],
    "big_task": ["project"],
}


def regenerate_kp_with_llm(kp_key: str, current: str, instruction: str, mods: dict) -> str:
    """单知识点板块重新生成（LLM），返回新文本。"""
    from ai_analysis.services import get_llm

    if kp_key not in _KP_DEFINITIONS:
        raise ValueError(f"未知知识点: {kp_key}")
    context_parts = []
    for key in _KP_CONTEXT_KEYS.get(kp_key, []):
        val = mods.get(key)
        text = val if isinstance(val, str) else ""
        if isinstance(val, dict):
            text = "\n".join(
                p for p in [
                    val.get("title"), val.get("content"), val.get("grammar_tip"),
                    val.get("sound"),
                ] if p
            )
        if text:
            context_parts.append(f"【{key}】\n{text}")
    prompt = REGENERATE_KP_PROMPT.format(
        kp_label=_KP_LABELS[kp_key],
        definition=_KP_DEFINITIONS[kp_key],
        context="\n\n".join(context_parts)[:8000] or "（无相关教材内容）",
        current=current or "（空）",
        instruction=instruction or "按定义重新生成",
    )
    try:
        llm = get_llm(feature="default", temperature=0.3)
        return (llm.invoke(prompt).content or "").strip()
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"AI 重新生成失败: {exc}") from exc


VOCAB_IPA_PROMPT = """# 任务
请给以下英语单词标注 IPA 音标并给出中文释义（注意是中文！6字以内），输出格式化文本。

# 规则
- **单词**（单个词，如 kite-flying、hopscotch）标注 IPA 音标，格式：word /ˈhɒpskɒtʃ/ 跳房子
- **短语**（含空格或多个词，如 tug of war、Chinese yo-yo、take in）**不标音标**，原样保留
- 每项一行，不要编号，不要 JSON，不要解释
- 如果某个单词的 IPA 不确定，照常标注（用常见英式/美式发音皆可）

# 单词列表
{words}"""


def add_ipa_to_vocabulary(words: list) -> str:
    """LLM 给单词列表补 IPA 音标（短语不标）。失败返回空串（调用方回退规则文本）。"""
    from ai_analysis.services import get_llm

    if not words:
        return ""
    prompt = VOCAB_IPA_PROMPT.format(words="\n".join(words))
    try:
        llm = get_llm(feature="default", temperature=0.1)
        return (llm.invoke(prompt).content or "").strip()
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[corpus] IPA 标注失败（回退规则文本）: {exc}")
        return ""
