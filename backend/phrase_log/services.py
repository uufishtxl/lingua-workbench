import os
from typing import List

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from .types import LookupRequestData, LookupResponseItem, LLMResponse

load_dotenv()

is_using_deepseek = os.getenv("MODEL_NAME") == "deepseek-chat"

llm = None

if is_using_deepseek:
    llm = ChatOpenAI(
        model=os.getenv("MODEL_NAME"),
        base_url=os.getenv("BASE_URL"),
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        temperature=0
    )
else:
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("MODEL_NAME"), 
        google_api_key=os.getenv("GOOGLE_API_KEY"), 
        temperature=0,
        # 如果遇到输出被截断或报错，可以尝试调整 safety_settings
        # safety_settings={...} 
    )

llm_as_structured = llm.with_structured_output(LLMResponse, method="function_calling")


def preprocess_input(inputs: dict) -> dict:
    exp_str = inputs["expressions_to_lookup"]
    exp_snippets = [exp.strip() for exp in exp_str.split("/")]
    print("exp snippets are {exp_snippets}")
    remark = inputs.get("remark")
    remark_instruction = ""
    if remark:
        remark_instruction = f"备注参考：{remark}。如果表达匹配备注中的 expression，请用自己的话总结 note 内容作为 remark 字段。"
    return {
        "sentence": inputs["original_context"],
        "cleaned_exp_str": " / ".join(exp_snippets),
        "exp_count": len(exp_snippets),
        "first_exp_to_lookup": exp_snippets[0],
        "remark_instruction": remark_instruction
    }

system_prompt = "You are an expert English-Chinese bilingual assistant. Your task is to explain English expressions in context for a learner. You MUST respond ONLY with valid, perfectly formed JSON."

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一位专业的英汉双语助手，帮助英语学习者理解语境中的英语表达。"),
    ("human", """我正在学习英语，碰到了这句话：
"{sentence}"

我对其中的这些表达不太理解：{cleaned_exp_str}

请帮我解释每个表达：
1. 给出中文释义（500字符以内，如果表达已过时请说明现代替代语）
2. 提供一个经典例句
3. 如有 typo 请修正

{remark_instruction}
""")
])

chain = RunnableLambda(preprocess_input) | prompt | llm_as_structured | (lambda x: x.model_dump().get("explanations", []))

# 发送不理解的句子和短语给 Deepseek
def get_structured_explanations(lookup: LookupRequestData) -> List[LookupResponseItem]:
    """使用 LCEL chain 调用 Deepseek 获取短语解释"""
    try:
        return chain.invoke(lookup)
    except Exception as e:
        print(f"Chain invocation error: {e}")
        return None


