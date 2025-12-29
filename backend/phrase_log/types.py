from typing import TypedDict, List, Optional

from pydantic import BaseModel, Field


class ExpressionRemark(TypedDict):
    expression: str
    note: str


"""
lookup_data = {
    "original_context": "For your information, ass-munch, I've lost four pounds."
    "expressions_to_lookup": "for your information / as munch",
    "tags": ["Daily"]
    "remark": [{"expression": "for your information", "note": "For your information 与 For the record / Let me get it straight 的区别和语气严重程度"}]
}
"""

class LookupRequestData(TypedDict):
    original_context: str
    expressions_to_lookup: str
    tags: Optional[List[str]]
    remark: Optional[List[ExpressionRemark]]


class LookupResponseItem(BaseModel):
    original_context: str = Field(description="原始句子")
    expression_text: str = Field(description="被查询的短语")
    chinese_meaning: str = Field(description="中文释义，500字符以内，如表达已过时请说明现代替代语")
    example_sentence: str = Field(description="一个经典使用范例")
    remark: str = Field(default="", description="个人笔记总结")

class LLMResponse(BaseModel):
    explanations: List[LookupResponseItem]
