from openai import OpenAI, APIError
from decouple import config
from typing import List
from .types import LookupRequestData, LookupResponseData
import json


# 发送不理解的句子和短语给 Deepseek
def get_structured_explanations (lookup: LookupRequestData) -> List[LookupResponseData]:
    """
    
    """
    # 动态生成 Prompt
    sentence = lookup["original_context"]
    expression_str = lookup["expressions_to_lookup"]
    remark=lookup["remark"]
    expression_str_list = [exp.strip() for exp in expression_str.split("/")]
    cleaned_exp_str = " / ".join(expression_str_list)
    exp_count = len(expression_str_list)

    # 系统提示，告诉 AI 他的角色
    system_prompt = "You are an expert English-Chinese bilingual assistant. Your task is to explain English expressions in context for a learner. You MUST respond ONLY with valid, perfectly formed JSON."

    # 用户提示
    user_prompt = f"""
    我正在学习英语。碰到了这样一句句子：
    “{sentence}”

    我对这句话中的以下 {exp_count}个词语表达不太理解：
    {cleaned_exp_str}

    如果我提供的上述英语中有typo error，请及时修正。

    你能帮助我吗？请严格按照以下要求返回一个 JSON 对象。
    1. 根对象必须有一个唯一的键，名为 "explanations"
    2. "explanations" 的值必须是一个 JSON 列表
    3. 这个列表的长度必须是 {exp_count}
    4. 列表中的每一个字典元素都必须包含且仅包含以下五个键：
       - "original_context": 必须是 "{sentence}"
       - "expression_text": 对应的被查询的短语：(e.g., "{expression_str_list[0]}")
       - "chinese_meaning": 对该短语的中文解释，控制在500字符以内（如果该短语已不再普遍使用，请说明目前流行的替代语。比如hunk of beef不再流行，取而代之的是hunk。
       - "example_sentence": 一个新的、经典的使用范例（句子）
       - "remark": 请参考"remark" 列表，比如 {remark}。在处理每个短语时，请检查其 "expression_text"是否与列表中任何对象的 "expression" 字段值匹配。如果匹配，请根据该对象的 "note" 字段内容，为此 "remark" 字段生成一段总结性的个人笔记（尽量短一点）。请您用自己的话总结，而不是照搬“note”里的原话。如果不匹配或 "备注列表" 为空，则返回空字符串""
    """

    print("--- Sendinig Prompt to AI ---")
    print(user_prompt)
    print("------------------------------")

    try:
        base_url = config("DEEPSEEK_BASE_URL")
        api_key = config("DEEPSEEK_API_KEY")

        # 构造请求
        client = OpenAI(api_key=api_key, base_url=base_url)

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=False,
            # 强制 AI 返回 JSON
            response_format={"type": "json_object"}
        )
        message_content = response.choices[0].message.content

        if message_content is None:
            print("API Error: Received empty response from AI")
            return None

        parsed_data = json.loads(message_content)
        explanation_list = parsed_data.get("explanations")

        if not explanation_list or not isinstance(explanation_list, list):
            print(f"API Error: AI did not return the expected 'explanations' list")
            return None
        
        return explanation_list
    
    except APIError as e:
        print(f"Deepseek API error occurred: {e}")
        return None
    except json.JSONDecodeError:
        print(f"API Error: Failed to decode AI's JSON response. Response was: {message_content}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


