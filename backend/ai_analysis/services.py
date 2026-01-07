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


# ============ Dictionary Lookup ============
from .schemas import DictionaryResponse
from .prompts import DICTIONARY_SYSTEM_PROMPT, DICTIONARY_HUMAN_PROMPT

_dictionary_structured_llm = None
_dictionary_chain = None


def get_dictionary_structured_llm():
    """Get the singleton structured LLM for dictionary responses."""
    global _dictionary_structured_llm
    if _dictionary_structured_llm is None:
        llm = get_llm()
        _dictionary_structured_llm = llm.with_structured_output(
            DictionaryResponse,
            method="function_calling"
        )
    return _dictionary_structured_llm


def get_dictionary_chain():
    """
    Get the singleton LCEL chain for dictionary lookup.
    Returns a chain that takes {full_context, word_or_phrase}
    and returns a DictionaryResponse.
    """
    global _dictionary_chain
    if _dictionary_chain is None:
        structured_llm = get_dictionary_structured_llm()
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
    """
    Look up a word or phrase and return dictionary entry.
    
    Args:
        full_context: The complete sentence/context
        word_or_phrase: The word/phrase to look up
    
    Returns:
        DictionaryResponse with definition and examples
    """
    chain = get_dictionary_chain()
    
    result = chain.invoke({
        "full_context": full_context,
        "word_or_phrase": word_or_phrase
    })
    
    return result


# ============ Refresh Example ============
from .schemas import RefreshExampleResponse
from .prompts import REFRESH_EXAMPLE_SYSTEM_PROMPT, REFRESH_EXAMPLE_HUMAN_PROMPT

_refresh_example_structured_llm = None
_refresh_example_chain = None


def get_refresh_example_structured_llm():
    """Get the singleton structured LLM for refresh example responses."""
    global _refresh_example_structured_llm
    if _refresh_example_structured_llm is None:
        llm = get_llm()
        _refresh_example_structured_llm = llm.with_structured_output(
            RefreshExampleResponse,
            method="function_calling"
        )
    return _refresh_example_structured_llm


def get_refresh_example_chain():
    """Get the singleton LCEL chain for refreshing examples."""
    global _refresh_example_chain
    if _refresh_example_chain is None:
        structured_llm = get_refresh_example_structured_llm()
        prompt = ChatPromptTemplate.from_messages([
            ("system", REFRESH_EXAMPLE_SYSTEM_PROMPT),
            ("human", REFRESH_EXAMPLE_HUMAN_PROMPT),
        ])
        _refresh_example_chain = prompt | structured_llm
    
    return _refresh_example_chain


def refresh_example(
    word_or_phrase: str,
    definition: str,
    original_context: str
) -> RefreshExampleResponse:
    """
    Generate a new example sentence for a word/phrase.
    
    Args:
        word_or_phrase: The word/phrase to generate example for
        definition: The Chinese definition of the word/phrase
        original_context: The original sentence context
    
    Returns:
        RefreshExampleResponse with new example
    """
    chain = get_refresh_example_chain()
    
    result = chain.invoke({
        "word_or_phrase": word_or_phrase,
        "definition": definition,
        "original_context": original_context
    })
    
    return result
