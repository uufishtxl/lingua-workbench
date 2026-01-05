"""
Pydantic models for AI analysis responses.
These are used for LangChain structured output.
"""
from typing import Literal, List
from pydantic import BaseModel, Field


class ScriptSegment(BaseModel):
    """单个音节片段的分析结果"""
    original: str = Field(description="focus_segment中的文字片段")
    sound_display: str = Field(description="快速能够阅读的标志，比如 Yuh，而不是用音标 /yə/")
    ipa: str = Field(description="IPA音标，比如 /yə/")
    is_stressed: bool = Field(description="是否重读")


class SoundScriptResponse(BaseModel):
    """听觉图谱分析响应"""
    card_type: Literal["visual_sound_script"] = Field(
        default="visual_sound_script",
        description="卡片类型"
    )
    speed_profile: Literal["native_fast", "native_normal"] = Field(
        description="极速语流/普通语流"
    )
    full_context: str = Field(description="完整的上下文内容")
    focus_segment: str = Field(description="完整上下文中需要聚焦的文字片段")
    phonetic_tags: List[str] = Field(
        description="最关键的语音特点标签（1-3个），比如 Reduction / Linking / Assimilation"
    )
    phonetic_tag_notes: List[str] = Field(
        description="与phonetic_tags对应的说明列表，用中文解释每个语音特点在focus_segment中的体现"
    )
    script_segments: List[ScriptSegment] = Field(
        description="按词/音节拆分的发音信息"
    )


class ExampleSentence(BaseModel):
    """例句"""
    english: str = Field(description="英文例句")
    chinese: str = Field(description="中文翻译")


class DictionaryResponse(BaseModel):
    """字典查询响应"""
    card_type: Literal["dictionary"] = Field(
        default="dictionary",
        description="卡片类型"
    )
    word_or_phrase: str = Field(description="查询的单词或短语")
    part_of_speech: str = Field(description="词性，如 noun, verb, phrase")
    definition_en: str = Field(description="英文释义")
    definition_cn: str = Field(description="中文释义")
    examples: List[ExampleSentence] = Field(
        description="例句列表（1-2个）"
    )
    usage_note: str = Field(description="用法说明（可选），如语境、语气等")


class RefreshExampleResponse(BaseModel):
    """刷新例句响应"""
    word_or_phrase: str = Field(description="单词或短语")
    example: ExampleSentence = Field(description="新生成的例句")
