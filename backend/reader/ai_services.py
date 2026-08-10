import time
import logging

from langchain_core.prompts import ChatPromptTemplate
from ai_analysis.services import get_llm as _get_llm
from .schemas import ArticleMetaResponse, CopilotResponse, AnnotationContext

logger = logging.getLogger(__name__)

# ============ Article Background Analysis (Gemini) ============

_article_meta_chain = None

def get_article_meta_chain():
    global _article_meta_chain
    if _article_meta_chain is None:
        llm = _get_llm(feature="article_meta")
        structured_llm = llm.with_structured_output(
            ArticleMetaResponse,
            method="function_calling"
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert reading comprehension assistant. Analyze the provided article text and extract its generic metadata. Be concise. The text provided will have paragraph indices like [ID] Text. Use these IDs to set the start and end indices of your outline segments. CRITICAL REQUIREMENT: You MUST generate a non-empty `outline` array. Even if the article is very short, create at least one outline segment covering the entire text."),
            ("human", "Article Title: {title}\n\nArticle Text:\n{text}\n\nExtract the domain, a 2-sentence summary, the difficulty level, and a mandatory detailed chronological outline mapping the start and end paragraph IDs.")
        ])
        _article_meta_chain = prompt | structured_llm
    return _article_meta_chain

def analyze_article_meta(title: str, text: str) -> dict:
    chain = get_article_meta_chain()
    # Truncate text if it's absurdly long, though Gemini handles 1M+ tokens
    text = text[:50000] 
    res = chain.invoke({"title": title, "text": text})
    return {
        "domain": res.domain,
        "summary": res.summary,
        "difficulty": res.difficulty,
        "outline": [
            {
                "title": item.title,
                "start_index": item.start_index,
                "end_index": item.end_index
            } for item in res.outline
        ] if getattr(res, 'outline', None) else []
    }

# ============ Copilot Annotation Assist (DeepSeek) ============

_copilot_llm = None

def get_copilot_llm():
    """
    Get the LLM for reader copilot (Uses DeepSeek).
    Uses raw LLM instead of with_structured_output
    to avoid DeepSeek v4 thinking mode / tool_choice conflicts.
    """
    global _copilot_llm
    if _copilot_llm is None:
        _copilot_llm = _get_llm()
    return _copilot_llm

MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

def assist_annotation(ctx: AnnotationContext) -> dict:
    llm = get_copilot_llm()
    
    system_instructions = """You are an expert bilingual (English/Chinese) AI reading copilot. 
The user is reading an article on the domain: {domain}.
They selected a text snippet and assigned a specific annotation type. Their annotation type determines how you should explain the text.

If Type is 'yellow' (Jargon, or any scenario the user asks about):
- ALWAYS start your response with the phrase's American English phonetic spelling (Merriam-Webster style, wrapped in \\) like `\\ˈjar-gən\\`.
- Explain the word's basic definition, and if it has jargon/terminology usage explain that too, but crucially provide its exact meaning in this specific context (including tone, metaphor, symbolism, etc.).
- Use simple Chinese.
- Please always give an explanation. Do not leave it blank or omitted.
- CRITICAL: Keep your response extremely concise, under 100 words/characters. No long intros.

If Type is 'blue' (Usage/Phrasing):
- Explain why this phrasal structure, idiom, or word choice is used here.
- What nuance does it carry?
- Provide 1 brief, new example sentence.
- CRITICAL: Keep your explanation extremely concise, under 100 words/characters (plus the example).

If Type is 'pink' (Thought/Question):
- The user has a specific thought or "Socratic question" about the text.
- Directly answer or discuss their question based on the paragraph context.
- Encourage deep thinking.
- Do not end with a question. No further interaction is wanted.

Output Rules:
- Return a valid HTML string directly in the `content` field.
- Use light semantic HTML tags (e.g., <strong>, <em>, <ul>, <br>) for formatting.
- Do NOT wrap in generic markdown code blocks, just return HTML.
- Do NOT output JSON. Just output the HTML content directly."""

    human_msg = f"""Paragraph Context:
{ctx.paragraph}

Selected Text: "{ctx.selected_text}"
Annotation Type: {ctx.annotation_type}
User's Note: {ctx.user_note or "No specific note provided. Just explain in Chinese."}"""

    from langchain_core.messages import SystemMessage, HumanMessage
    messages = [
        SystemMessage(content=system_instructions.format(domain=ctx.domain or "General")),
        HumanMessage(content=human_msg)
    ]

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = llm.invoke(messages)
            if response is None:
                raise ValueError("LLM returned None")
            content = response.content.strip()
            return {"content": content}
        except Exception as e:
            last_error = e
            logger.warning(f"assist_annotation attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

    logger.error(f"assist_annotation all {MAX_RETRIES} attempts failed: {last_error}")
    return {
        "error": True,
        "message": f"AI 服务暂时不可用，请稍后重试。"
    }

