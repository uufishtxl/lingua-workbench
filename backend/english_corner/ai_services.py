"""
AI Services for English Corner.

Provides:
  - Tutor feedback (polish + explanation)
  - Character reply (scene-driven roleplay)
  - TTS audio generation (Gemini 2.5 Flash Preview TTS)
  - Flashcard generation (structured Q&A)
  - Scenario prompt synthesis
  - WordNode enrichment (explanation + example)
"""
import os
import json
import wave
import logging
import traceback
from enum import Enum
from typing import Literal

from django.conf import settings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from pydantic import BaseModel, Field
from ai_analysis.services import _get_llm

logger = logging.getLogger(__name__)

# ================================================================
# Constants
# ================================================================
HISTORY_WINDOW = 10  # Load this many recent messages for LLM context


# ================================================================
# History Helpers
# ================================================================

def _build_history(conversation, exclude_message_id=None):
    """
    Build a sliding window of recent messages for LLM context.
    Always loads the last HISTORY_WINDOW messages.
    Returns list of (role, content) tuples for LangChain MessagesPlaceholder.
    """
    from .models import PracticeMessage

    qs = conversation.messages.filter(
        status__in=['SUCCESS', 'PROCESSING']
    ).order_by('-created_at')

    if exclude_message_id:
        qs = qs.exclude(id=exclude_message_id)

    recent = list(qs[:HISTORY_WINDOW])
    recent.reverse()  # Chronological order

    history = []
    for msg in recent:
        if msg.role == PracticeMessage.Role.USER:
            history.append(("human", msg.user_content))
        else:
            history.append(("ai", msg.character_content))
    return history


# ================================================================
# 1. Tutor Feedback — Polish + Chinese Explanation
# ================================================================

TUTOR_SYSTEM_PROMPT = """You are a professional English tutor. The student is practicing English conversation.

Your ONLY job is to:
1. Polish their English text to sound more natural and native-like.
2. Provide a concise Chinese explanation of key corrections and improvements.

IMPORTANT: You MUST respond with ONLY a valid JSON object in this exact format:
{{"polished_text": "...", "explanation_cn": "..."}}

Rules:
- polished_text: The improved version of the student's text. Keep the original meaning.
- explanation_cn: 2-3 sentences in Chinese explaining what was changed and why.
- Do NOT include any text outside the JSON object.
- If the student's text is already perfect, return it as-is and note that in explanation_cn."""


def generate_tutor_feedback(conversation, user_text: str) -> dict:
    """
    Call LLM as Tutor to polish user text and provide Chinese explanation.
    Returns: {"polished_text": "...", "explanation_cn": "..."}
    """
    llm = _get_llm(feature="english_corner", temperature=0.3)
    prompt = ChatPromptTemplate.from_messages([
        ("system", TUTOR_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="history"),
        ("human", "Please polish and explain the following student input:\n\n{input}")
    ])

    chain = prompt | llm
    history = _build_history(conversation)

    response = chain.invoke({"input": user_text, "history": history})
    content = response.content.strip()

    # Parse JSON response
    # Clean markdown fences if present
    if content.startswith("```"):
        content = content.split("\n", 1)[-1]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    try:
        result = json.loads(content)
        return {
            "polished_text": result.get("polished_text", user_text),
            "explanation_cn": result.get("explanation_cn", ""),
        }
    except json.JSONDecodeError:
        logger.warning(f"Tutor feedback JSON parse failed: {content}")
        return {"polished_text": user_text, "explanation_cn": "（解析失败）"}


# ================================================================
# 2. Character Reply — Scene-driven roleplay
# ================================================================

CHARACTER_SYSTEM_TEMPLATE = """You are roleplaying as the following character in an English conversation practice scenario.

SCENARIO: {title}
SETTING: {description}
CHARACTER INSTRUCTIONS: {system_prompt}

Rules:
- Stay in character at all times.
- Use natural, conversational English appropriate to the character.
- Keep responses concise (under 100 words) to maintain a chat-like feel.
- If this is the first message (user input is empty or says "greeting"), start with a warm, in-character greeting.
- Drive the conversation forward by asking follow-up questions or introducing scenario-relevant topics."""


def generate_character_reply(conversation, user_text: str = "") -> str:
    """
    Call LLM as the scene Character to generate a reply.
    Returns: character reply text string.
    """
    scenario = conversation.scenario
    llm = _get_llm(feature="english_corner", temperature=0.7)

    system_msg = CHARACTER_SYSTEM_TEMPLATE.format(
        title=scenario.title,
        description=scenario.description,
        system_prompt=scenario.system_prompt,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_msg),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])

    chain = prompt | llm
    history = _build_history(conversation)

    llm_input = user_text if user_text else (
        "Please start the conversation with a friendly greeting in character."
    )

    response = chain.invoke({"input": llm_input, "history": history})
    return response.content.strip()


# ================================================================
# 3. TTS Audio Generation — Gemini 2.5 Flash Preview TTS
# ================================================================

def generate_tts_audio(text: str, conversation_id: int, message_id: int) -> str:
    """
    Use google.genai Client to call gemini-2.5-flash-preview-tts.
    Generates 24kHz, 16-bit, Mono WAV.
    Returns: relative media URL (e.g. 'english_corner/tts/42/123.wav')
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        logger.error("google-genai SDK not installed. pip install google-genai")
        return ""

    client = genai.Client()

    tts_response = client.models.generate_content(
        model='gemini-2.5-flash-preview-tts',
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Puck"
                    )
                )
            )
        )
    )

    # Extract audio data from response
    for part in tts_response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.mime_type.startswith("audio/"):
            audio_data = part.inline_data.data

            # Build the save path
            rel_dir = os.path.join('english_corner', 'tts', str(conversation_id))
            abs_dir = os.path.join(settings.MEDIA_ROOT, rel_dir)
            os.makedirs(abs_dir, exist_ok=True)

            filename = f"{message_id}.wav"
            abs_path = os.path.join(abs_dir, filename)
            rel_url = f"{rel_dir}/{filename}"

            # Write WAV with proper RIFF header
            with wave.open(abs_path, "wb") as wav_file:
                wav_file.setnchannels(1)       # Mono
                wav_file.setsampwidth(2)       # 16-bit
                wav_file.setframerate(24000)   # 24kHz
                wav_file.writeframes(audio_data)

            logger.info(f"TTS audio saved: {abs_path}")
            return rel_url

    logger.warning("No audio data found in TTS response")
    return ""


# ================================================================
# 4. Flashcard Generation — Structured Q&A card
# ================================================================

FLASHCARD_SYSTEM_PROMPT = """You are an English learning assistant. The student has highlighted a phrase from a conversation.

Generate a structured flashcard for spaced repetition review.

IMPORTANT: You MUST respond with ONLY a valid JSON object in this exact format:
{{"target_phrase": "...", "prompt_question": "...", "answer": "...", "example_context": "..."}}

Rules:
- target_phrase: The exact highlighted phrase.
- prompt_question: A fill-in-the-blank or contextual prompt in English that tests knowledge of this phrase. Should be challenging but fair.
- answer: The expected answer (the phrase itself or its usage).
- example_context: A natural example sentence using the phrase in a different context than the original."""


def generate_flashcard(text: str, context: str = "") -> dict:
    """
    Call LLM to generate a structured flashcard from highlighted text.
    Returns: {"target_phrase", "prompt_question", "answer", "example_context"}
    """
    llm = _get_llm(feature="english_corner", temperature=0.5)
    prompt = ChatPromptTemplate.from_messages([
        ("system", FLASHCARD_SYSTEM_PROMPT),
        ("human", "Highlighted text: \"{text}\"\nOriginal context: \"{context}\"")
    ])

    chain = prompt | llm
    response = chain.invoke({"text": text, "context": context})
    content = response.content.strip()

    # Clean markdown fences
    if content.startswith("```"):
        content = content.split("\n", 1)[-1]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        logger.warning(f"Flashcard JSON parse failed: {content}")
        return {
            "target_phrase": text,
            "prompt_question": f'What does "{text}" mean?',
            "answer": text,
            "example_context": context,
        }


# ================================================================
# 5. Scenario Prompt Synthesis
# ================================================================

SCENARIO_PROMPT_SYSTEM = """You are a prompt engineer. Given a scenario title and description/vibe, create a detailed system prompt for an AI roleplay character.

The prompt should:
- Define the character's role, personality, and speaking style.
- Set the scene and context.
- Include instructions for maintaining character consistency.
- Be written in English.
- Be 3-5 sentences.

Return ONLY the system prompt text, nothing else."""


def generate_scenario_prompt(title: str, description: str) -> str:
    """
    Generate a system prompt for a scenario from its title and description.
    """
    llm = _get_llm(feature="english_corner", temperature=0.7)
    prompt = ChatPromptTemplate.from_messages([
        ("system", SCENARIO_PROMPT_SYSTEM),
        ("human", "Title: {title}\nDescription/Vibe: {description}")
    ])

    chain = prompt | llm
    response = chain.invoke({"title": title, "description": description})
    return response.content.strip()


# ================================================================
# 6. WordNode Enrichment — Explanation + Example
# ================================================================

WORD_ENRICHMENT_PROMPT = """You are an English learning assistant. Given a word or phrase, provide:
1. A clear and concise Chinese explanation (释义).
2. A natural English example sentence demonstrating its use.

IMPORTANT: You MUST respond with ONLY a valid JSON object:
{{"explanation": "...(中文释义)...", "example": "...(English example sentence)..."}}"""


def generate_word_enrichment(label: str, context: str = "") -> dict:
    """
    Call LLM to generate explanation + example for a word/phrase.
    Returns: {"explanation": "...", "example": "..."}
    """
    llm = _get_llm(feature="english_corner", temperature=0.3)
    prompt = ChatPromptTemplate.from_messages([
        ("system", WORD_ENRICHMENT_PROMPT),
        ("human", "Word/Phrase: \"{label}\"\nContext: \"{context}\"")
    ])

    chain = prompt | llm
    response = chain.invoke({"label": label, "context": context})
    content = response.content.strip()

    if content.startswith("```"):
        content = content.split("\n", 1)[-1]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        logger.warning(f"Word enrichment JSON parse failed: {content}")
        return {"explanation": "（生成失败）", "example": ""}


# ================================================================
# 7. Batch Scenario Generation — Daily Phrases
# ================================================================

ALLOWED_CONTEXT_TAGS = [
    "Office", "Meeting", "Interview", "Remote_Work", "Cafe", 
    "Restaurant", "Party", "Street", "Home", "Shopping", 
    "Gym", "Commute", "Airport", "Hospital", "Hotel", 
    "Texting", "Phone_Call"
]

# Create a dynamic Enum for Pydantic validation
# 第一个参数：生成的枚举类的类名；第二个参数：字典推导式定义了美剧的成员名（KEY）和成员值（VALUE）
ContextTag = Enum("ContextTag", {tag.upper(): tag for tag in ALLOWED_CONTEXT_TAGS}, type=str)

BATCH_SCENARIO_SYSTEM_PROMPT = f"""Act as an expert linguist and language tutor. I will provide a JSON array of vocabulary words or phrases. For each item, generate exactly 3 distinct, practical, real-world contexts where this word is naturally used.

Constraints:
- Keep each scenario description brief (maximum 15 words).
- Do not include the definition of the word.
- You MUST assign one context tag to each scenario from the following exact list: {ALLOWED_CONTEXT_TAGS}. Do not invent new tags."""

class ScenarioItem(BaseModel):
    description: str = Field(description="A brief description of the scenario (max 15 words).")
    tag: ContextTag = Field(description="The context tag from the allowed list.")

class WordScenarios(BaseModel):
    word: str = Field(description="The original vocabulary word requested.")
    scenarios: list[ScenarioItem] = Field(description="List of exactly 3 distinct scenarios for this word.")

class BatchScenarioResult(BaseModel):
    results: list[WordScenarios] = Field(description="The list of results for all requested words.")

def generate_batch_scenarios(words: list[dict]) -> dict:
    """
    Generate scenarios for multiple words in a single LLM call.
    Returns: A dictionary mapping word labels to lists of scenario dicts.
    """
    llm = _get_llm(feature="english_corner").with_structured_output(BatchScenarioResult, method="function_calling")
    prompt = ChatPromptTemplate.from_messages([
        ("system", BATCH_SCENARIO_SYSTEM_PROMPT),
        ("human", "{input}")
    ])

    word_labels = [w['label'] for w in words]
    
    # Use LCEL with a dictionary-based mapper for cleaner JSON serialization
    chain = (
        {"input": lambda labels: json.dumps(labels, ensure_ascii=False)} 
        | prompt 
        | llm
    )
    
    try:
        response: BatchScenarioResult = chain.invoke(word_labels)
        data = response.model_dump()
        return {item["word"]: item["scenarios"] for item in data["results"]}
    except Exception as e:
        logger.exception(f"Batch scenario structured output failed: {e}")
        return {}


# ================================================================
# 8. Sentence Verification — Daily Phrases
# ================================================================

VERIFY_SENTENCE_SYSTEM_PROMPT = """You are a Native English Teacher living in the United States. A student is practicing vocabulary by writing original sentences.

You will receive:
- target_word: the vocabulary word the student must use
- user_sentence: the student's original sentence
- bonus_words: a list of extra vocabulary words (with IDs)

Your tasks:
1. Determine if the student used the target_word correctly and naturally in context. Set is_pass to true or false.
2. Polish the student's sentence (minimal grammatical corrections) into `polished_text`.
3. Provide a `native_version`: Reimagine the sentence as a native speaker would naturally say it in the given context. CRITICAL: Prioritize natural flow and common idioms over the student's original structure.
4. Provide a `community_version`: The 'Internet-native' or 'Street-smart' way to say this. Think Reddit, Hacker News, or X. Use sharp metaphors, internet slang, and high-impact verbs. It should sound like someone who is 'over' the corporate BS and tells it like it is.
5. Provide brief, encouraging feedback (1-2 sentences).
6. Check each bonus_word — if they used it naturally (or creatively adapted it), include its ID in mastered_word_ids. IMPORTANT: The student might make creative wordplay (e.g. 'AI rush' instead of 'gold rush'). Do NOT 'correct' their creative adaptations back to the dictionary form.
6. ALWAYS provide 1-3 natural, high-leverage alternatives (idioms, phrases, or collocations).
   - These alternatives should relate broadly to the theme or intent of the user's sentence. They do NOT need to perfectly substitute the text in the exact original grammar context. Be flexible.
   - Dynamic "Vibe" Labeling: Label each with its specific context (e.g., "SHARP & CRITICAL", "CONVERSATIONAL", "BUSINESS / TECH").
   - For each alternative, provide the "expression" (the alternative phrase) and an "example" (one clear sentence showing it in action). 
     CRITICAL: For the "example" sentences, INVENT COMPLETELY NEW, DIVERSE CONTEXTS (e.g. workplace, daily life, travel, movies). Do NOT just reuse the precise topic of the student's original sentence. We want exposure to diverse situations."""

class AlternativeItem(BaseModel):
    vibe: str = Field(description="Dynamic vibe labeling, e.g. CONVERSATIONAL, BUSINESS / TECH")
    expression: str = Field(description="The alternative phrase, idiom, or collocation.")
    example: str = Field(description="A completely new, diverse context sentence showing it in action.")

class VerificationResult(BaseModel):
    is_pass: bool = Field(description="Whether the target_word was used correctly and naturally.")
    polished_text: str = Field(description="Minimal grammatical corrections of the user's sentence.")
    native_version: str = Field(description="Reimagine the sentence as a native speaker would naturally say it in the given context. CRITICAL: Prioritize natural flow and common idioms over the student's original structure. If the student used a good phrase, keep it ONLY if it's the most natural choice available. If a better, more idiomatic way exists (e.g., using a phrasal verb instead of a formal noun), prioritize the idiomatic version.")
    community_version: str = Field(description="The 'Internet-native' or 'Street-smart' way to say this. Think Reddit, Hacker News, or X. Use sharp metaphors, internet slang, and high-impact verbs. It should sound like someone who is 'over' the corporate BS and tells it like it is.")
    feedback: str = Field(description="Brief, encouraging feedback (1-2 sentences).")
    mastered_word_ids: list[int] = Field(description="List of integer bonus_word IDs that were successfully used.")
    alternatives: list[AlternativeItem] = Field(description="List of 1-3 natural, high-leverage alternatives.")

def verify_user_sentence(target_word: str, user_sentence: str, bonus_words: list[dict]) -> dict:
    """
    Call LLM to verify a user's sentence for Daily Phrases.
    Returns: A dictionary matching the VerificationResult schema.
    """
    llm = _get_llm(feature="english_corner").with_structured_output(VerificationResult, method="function_calling")
    prompt = ChatPromptTemplate.from_messages([
        ("system", VERIFY_SENTENCE_SYSTEM_PROMPT),
        ("human", "target_word: {target_word}\nuser_sentence: {user_sentence}\nbonus_words: {bonus_words}")
    ])

    # Cleaner LCEL pattern: JSON serialization of bonus_words is handled by the chain pipe itself
    chain = (
        RunnablePassthrough.assign(
            bonus_words=lambda x: json.dumps(x["bonus_words"], ensure_ascii=False)
        )
        | prompt 
        | llm
    )

    try:
        response: VerificationResult = chain.invoke({
            "target_word": target_word,
            "user_sentence": user_sentence,
            "bonus_words": bonus_words,
        })
        return response.model_dump()
    except Exception as e:
        logger.exception(f"Verify sentence structured output failed: {e}")
        return {
            "is_pass": False,
            "polished_text": user_sentence,
            "native_version": "",
            "feedback": "（评估失败，大模型服务暂时不可用，请重试）",
            "mastered_word_ids": [],
            "alternatives": [],
        }

