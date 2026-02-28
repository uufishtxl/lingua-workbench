from langchain_core.prompts import ChatPromptTemplate
from ai_analysis.services import _get_llm
from .schemas import ArticleMetaResponse, CopilotResponse, AnnotationContext

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

_copilot_chain = None

def get_copilot_chain():
    global _copilot_chain
    if _copilot_chain is None:
        llm = _get_llm()
        structured_llm = llm.with_structured_output(
            CopilotResponse,
            method="function_calling"
        )
        
        system_instructions = """
You are an expert bilingual (English/Chinese) AI reading copilot. 
The user is reading an article on the domain: {domain}.
They selected a text snippet and assigned a specific annotation type. Their annotation type determines how you should explain the text.

If Type is 'yellow' (Jargon):
- ALWAYS start your response with the phrase's American English phonetic spelling (Merriam-Webster style, wrapped in \\) like `\\ˈjar-gən\\`.
- Explain the domain-specific jargon or terminology.
- Provide its exact meaning in this context.
- Use simple Chinese.
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

Output Rules:
- Return a valid HTML string directly in the `content` field.
- Use light semantic HTML tags (e.g., <strong>, <em>, <ul>, <br>) for formatting.
- Do NOT wrap in generic markdown code blocks, just return HTML.
"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_instructions),
            ("human", "Paragraph Context:\n{paragraph}\n\nSelected Text: \"{selected_text}\"\nAnnotation Type: {annotation_type}\nUser's Note: {user_note}")
        ])
        _copilot_chain = prompt | structured_llm
    return _copilot_chain

def assist_annotation(ctx: AnnotationContext) -> dict:
    chain = get_copilot_chain()
    res = chain.invoke({
        "domain": ctx.domain or "General",
        "paragraph": ctx.paragraph,
        "selected_text": ctx.selected_text,
        "annotation_type": ctx.annotation_type,
        "user_note": ctx.user_note or "No specific note provided. Just explain in Chinese."
    })
    return {
        "content": res.content
    }

