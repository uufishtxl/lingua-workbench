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
    type: str = Field(description="音素类型，比如 Reduction / Linking / Assimilation")
    is_stressed: bool = Field(description="是否重读")
    note: str = Field(description="对发音的补充说明，比如'极速语流中v 音脱落'")


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
        description="最关键的音素标签（最多三种），比如 Reduction / Linking / Assimilation"
    )
    script_segments: List[ScriptSegment] = Field(
        description="关键音素详细描述"
    )
