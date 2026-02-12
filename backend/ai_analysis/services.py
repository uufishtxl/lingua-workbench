"""
LangChain services for AI analysis.
Contains the LCEL chains for different analysis types.
"""
import os
import json
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from .schemas import SoundScriptResponse, DictionaryResponse, RefreshExampleResponse
from .prompts import (
    SOUND_SCRIPT_SYSTEM_PROMPT, SOUND_SCRIPT_HUMAN_PROMPT,
    DICTIONARY_SYSTEM_PROMPT, DICTIONARY_HUMAN_PROMPT,
    REFRESH_EXAMPLE_SYSTEM_PROMPT, REFRESH_EXAMPLE_HUMAN_PROMPT
)


# ============ LLM Factories ============

_gemini_instance = None
_deepseek_instance = None

def get_gemini_llm():
    """Get the singleton Gemini LLM instance (for Analysis)."""
    global _gemini_instance
    if _gemini_instance is None:
        _gemini_instance = ChatGoogleGenerativeAI(
            model=os.getenv("MODEL_NAME", "gemini-2.5-flash"), 
            google_api_key=os.getenv("GOOGLE_API_KEY"), 
            temperature=0,
        )
    return _gemini_instance

def get_deepseek_llm():
    """Get the singleton DeepSeek LLM instance (for Dictionary & Translation)."""
    global _deepseek_instance
    if _deepseek_instance is None:
        _deepseek_instance = ChatOpenAI(
            model="deepseek-chat", # DeepSeek model name
            base_url=os.getenv("DEEPSEEK_BASE_URL"),
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            temperature=0
        )
    return _deepseek_instance


# ============ Sound Script (Gemini) ============

_sound_script_chain = None

def get_sound_script_chain():
    """
    Get the singleton LCEL chain for Sound Script analysis (Uses Gemini).
    """
    global _sound_script_chain
    if _sound_script_chain is None:
        llm = get_gemini_llm()
        structured_llm = llm.with_structured_output(
            SoundScriptResponse, 
            method="function_calling"
        )
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
    chain = get_sound_script_chain()
    return chain.invoke({
        "full_context": full_context,
        "focus_segment": focus_segment,
        "speed_profile": speed_profile
    })


# ============ Dictionary Lookup (DeepSeek) ============

_dictionary_chain = None

def get_dictionary_chain():
    """
    Get the singleton LCEL chain for dictionary lookup (Uses DeepSeek).
    """
    global _dictionary_chain
    if _dictionary_chain is None:
        llm = get_deepseek_llm()
        structured_llm = llm.with_structured_output(
            DictionaryResponse,
            method="function_calling" # DeepSeek supports tool calling? If not, might need JSON mode.
            # Fallback: If deepseek-chat doesn't support structured_output via tool/function calling perfectly via LangChain yet,
            # we might need standard JSON parsing. Assuming it works or using JSON mode.
            # DeepSeek V3/V2 supports function calling.
        )
        # Note: ChatOpenAI driver with DeepSeek usually handles this.
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", DICTIONARY_SYSTEM_PROMPT),
            ("human", DICTIONARY_HUMAN_PROMPT),
        ])
        _dictionary_chain = prompt | structured_llm
    
    return _dictionary_chain

def lookup_dictionary(
    full_context: str,
    word_or_phrase: str
) -> DictionaryResponse:
    chain = get_dictionary_chain()
    return chain.invoke({
        "full_context": full_context,
        "word_or_phrase": word_or_phrase
    })


# ============ Refresh Example (Gemini or DeepSeek? User said "Dictionary and this LLM use DeepSeek") ============
# Assuming Refresh Example belongs to "Dictionary/Translation" domain, let's use DeepSeek too.
# Or does it belong to "AI Analysis"? It generates examples.
# Let's stick to Gemini for this one as it was part of the original "Analysis" suite unless specified.
# User said "Dictionary and THIS LLM (translation) use DeepSeek". 
# Analysis uses Gemini. Refresh Example is kind of analysis/generative. Let's keep it on Gemini for now to overlap with current behavior, 
# unless loop-up failed.

_refresh_example_chain = None

def get_refresh_example_chain():
    global _refresh_example_chain
    if _refresh_example_chain is None:
        llm = get_gemini_llm() # Keep on Gemini
        structured_llm = llm.with_structured_output(
            RefreshExampleResponse,
            method="function_calling"
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", REFRESH_EXAMPLE_SYSTEM_PROMPT),
            ("human", REFRESH_EXAMPLE_HUMAN_PROMPT),
        ])
        _refresh_example_chain = prompt | structured_llm
    
    return _refresh_example_chain

def refresh_example(
    word_or_phrase: str,
    definition: str,
    original_context: str,
    current_example: str
) -> RefreshExampleResponse:
    chain = get_refresh_example_chain()
    return chain.invoke({
        "word_or_phrase": word_or_phrase,
        "definition": definition,
        "original_context": original_context,
        "current_example": current_example
    })


# ============ Batch Translation (DeepSeek) ============

_batch_translation_chain = None

def get_batch_translation_chain():
    """
    Get chain for batch translating a list of sentences.
    """
    global _batch_translation_chain
    if _batch_translation_chain is None:
        llm = get_deepseek_llm()
        
        # Simple Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a professional translator. You will receive a JSON list of objects with 'id' and 'text'. Translate the 'text' to Chinese (Simplified). Return a valid, minified JSON object with a single key 'translations' containing a list of {{id, translation}} objects. Do NOT output markdown code blocks."),
            ("human", "{json_input}")
        ])
        
        # We process raw JSON string output for robustness if structured output is flaky on lists
        _batch_translation_chain = prompt | llm
    
    return _batch_translation_chain

def batch_translate_idioms(slices_data: List[Dict]) -> List[Dict]:
    """
    Batch translate audio slices.
    
    Args:
        slices_data: List of dicts [{'id': 1, 'text': 'Hello'}, ...]
        
    Returns:
        List of dicts [{'id': 1, 'translation': '你好'}, ...]
    """
    if not slices_data:
        return []

    chain = get_batch_translation_chain()
    
    # Chunking: DeepSeek context is large, but to be safe let's process reasonable chunks or just one go if small.
    # Assuming frontend sends reasonable batch sizes (e.g. 50).
    
    json_input = json.dumps(slices_data, ensure_ascii=False)
    
    response_msg = chain.invoke({"json_input": json_input})
    content = response_msg.content.strip()
    
    # Clean up markdown if present
    if content.startswith("```json"):
        content = content.replace("```json", "", 1)
    if content.endswith("```"):
        content = content[:-3]
    
    try:
        result = json.loads(content)
        # Expecting {"translations": [...]}
        return result.get("translations", [])
    except json.JSONDecodeError as e:
        print(f"Batch translation JSON error: {e}, Content: {content}")
        return []

