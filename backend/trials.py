# %%
import os
from dotenv import load_dotenv

load_dotenv()
# %%
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
# %%
llm = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    temperature=0
)
# %%
from typing import Literal, List

class TargetTextResponseBase(BaseModel):
    card_type: Literal["visual_sound_script", "explanation_and_usage", "practice"] = Field(description="听觉图谱/释义与用法/小练习")


# %%
class ScriptSegment(BaseModel):
    original: str = Field(description="focus_segment中的文字片段")
    sound_display: str = Field(description="快速能够阅读的标志，比如 Yuh，而不是用音标 /yə/")
    ipa: str = Field(description="IPA音标，比如 /yə/")
    type: str = Field(description="音素类型，比如 Reduction / Linking / Assimilation")
    is_stressed: bool = Field(description="是否重读")
    note: str = Field(description="对发音的补充说明，比如'极速语流中v 音脱落'")

# %%
class SoundScriptResponse(TargetTextResponseBase):
    speed_profile: Literal["native_fast", "native_normal"] = Field(description="极速语流/普通语流")
    full_context: str = Field(description="完整的上下文内容")
    focus_segment: str = Field(description="完整上下文中需要聚焦的文字片段")
    phonetic_tags: List[str] = Field(description="最关键的音素标签（最多三种），比如 Reduction / Linking / Assimilation")
    script_segments: List[ScriptSegment] = Field(description="关键音素详细描述，与phonetic_tags一一对应")

# %%
structured_llm = llm.with_structured_output(SoundScriptResponse, method="function_calling")
# %%
system_template = """
You are an expert American English Dialect Coach specializing in "Connected Speech" and "Fast Casual Speech" (like in the TV show Friends).

YOUR TASK:
Analyze the user's provided [Focus Segment] within the [Full Context].
Generate a structured "Sound Script" that represents how a native speaker ACTUALLY sounds in a fast, conversational setting.

GUIDELINES FOR ANALYSIS:
1. **Speed Profile**: As provided by the user [Speed Profile]
2. **Sound Display (The "Ear" Test)**:
   - For `sound_display`, DO NOT use standard spelling. Use "Eye Dialect" or "Respellings" that mimic the sound.
   - Example: "You've" -> "Yuv" or "Yuhv" (if reduced).
   - Example: "going to" -> "gunna".
   - Example: "him" -> "im" (if h is dropped).
   - Example: "want to" -> "wanna".
3. **Phonetic Tags**: Identify the top 1-3 most prominent features (e.g., Flap T, Glottal Stop, Reduction, Linking, Elision, Assimilation).
4. **Card Type**: Always set `card_type` to "visual_sound_script" for this task.

CRITICAL RULES FOR `script_segments`:
- Break the [Focus Segment] down into natural phonetic chunks (usually words or linked groups).
- If a sound is dropped (like 'h' in 'him'), the `sound_display` must reflect that.
- If a word is stressed, set `is_stressed` to True. Content words (Nouns, Verbs) are usually stressed; Function words (pronouns, prepositions) are usually reduced.
"""
# %%
human_template = """
Full Context: "{full_context}"
Focus Segment: "{focus_segment}"
Speed Profile: "{speed_profile}"


Please analyze the Focus Segment.
"""
# %% [接在你的代码后面]
from langchain_core.prompts import ChatPromptTemplate

# 1. 定义 Prompt Template
prompt = ChatPromptTemplate.from_messages([
    ("system", system_template),
    ("human", human_template),
])

# 2. 组装 Chain
# input -> prompt -> structured_llm -> json object
chain = prompt | structured_llm

# 3. 准备测试数据
test_context = "It's up to you. It's your name. You've got to live with it."
test_focus = "You've got to"
test_speed_profile = "native_fast"

# 4. 运行
try:
    result = chain.invoke({
        "full_context": test_context,
        "focus_segment": test_focus,
        "speed_profile": test_speed_profile
    })
    
    # 打印结果看看 (美化打印)
    import json
    print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))

except Exception as e:
    print(f"Error: {e}")
# %%
