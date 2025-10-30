from typing import TypedDict, List


class LookupRequestData(TypedDict):
    original_context: str
    expressions_to_lookup: str

class LookupResponseData(TypedDict):
    original_context: str
    expression_text: str
    chinese_meaning: str
    example_sentence: str