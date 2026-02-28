from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

class MyResponse(BaseModel):
    function_calling_available: bool

llm = ChatOpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL"),
            model="deepseek-chat"
        )
structured_llm = llm.with_structured_output(MyResponse, method="function_calling")

SYS_INSTUCTION = """
你是一个 AI 助手。来帮助我看看 Deepseek 是否支持 function_calling。
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYS_INSTUCTION),
    ("human", "请根据实际情况回答")
])

chain = prompt | structured_llm
response = chain.invoke({})
print(response)