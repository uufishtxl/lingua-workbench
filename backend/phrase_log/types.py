from typing import TypedDict, List, Optional

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

class LookupResponseData(TypedDict):
    original_context: str
    expression_text: str
    chinese_meaning: str
    example_sentence: str
    remark: str