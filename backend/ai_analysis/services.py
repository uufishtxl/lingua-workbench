"""
LangChain services for AI analysis.
Contains the LCEL chains for different analysis types.
"""
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from .schemas import SoundScriptResponse
from .prompts import SOUND_SCRIPT_SYSTEM_PROMPT, SOUND_SCRIPT_HUMAN_PROMPT


# Singleton LLM instance
_llm_instance = None
_structured_llm_instance = None
_sound_script_chain = None


def get_llm():
    """Get the singleton LLM instance (lazy initialization)."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = ChatOpenAI(
            model="deepseek-chat",
            base_url="https://api.deepseek.com",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            temperature=0
        )
    return _llm_instance


def get_structured_llm():
    """Get the singleton structured LLM instance (lazy initialization)."""
    global _structured_llm_instance
    if _structured_llm_instance is None:
        llm = get_llm()
        _structured_llm_instance = llm.with_structured_output(
            SoundScriptResponse, 
            method="function_calling"
        )
    return _structured_llm_instance


def get_sound_script_chain():
    """
    Get the singleton LCEL chain for Sound Script analysis.
    Returns a chain that takes {full_context, focus_segment, speed_profile}
    and returns a SoundScriptResponse.
    """
    global _sound_script_chain
    if _sound_script_chain is None:
        structured_llm = get_structured_llm()
        prompt = ChatPromptTemplate.from_messages([
            ("system", SOUND_SCRIPT_SYSTEM_PROMPT),
            ("human", SOUND_SCRIPT_HUMAN_PROMPT),
        ])
        _sound_script_chain = prompt | structured_llm
    
    return _sound_script_chain


def analyze_sound_script(
    full_context: str,
    focus_segment: str,
    speed_profile: str = "native_fast"
) -> SoundScriptResponse:
    """
    Analyze a text segment and return the sound script.
    
    Args:
        full_context: The complete sentence/context
        focus_segment: The part to analyze
        speed_profile: "native_fast" or "native_normal"
    
    Returns:
        SoundScriptResponse with phonetic analysis
    """
    chain = get_sound_script_chain()
    
    result = chain.invoke({
        "full_context": full_context,
        "focus_segment": focus_segment,
        "speed_profile": speed_profile
    })
    
    return result
