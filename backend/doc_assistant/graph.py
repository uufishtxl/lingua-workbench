"""
LangGraph Multi-Agent Graph

Defines the Supervisor-Worker graph:
  Router → DocQA Agent / ScriptEditor Agent / General Chat
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from .state import AgentState
from .tools import (
    get_surrounding_lines, insert_script_line, edit_script_line, split_script_line, delete_script_line,
    get_reader_context, edit_reader_paragraph, edit_reader_annotation, delete_reader_annotation
)


from django.conf import settings
from langchain_openai import ChatOpenAI

# ── LLM Instances ──────────────────────────────────────────────
def _get_llm(feature="default", **kwargs):
    """Create an LLM instance based on settings.LLM_CONFIG for a specific feature."""
    # Try formatted feature key, fallback to default (SETTINGS.PY DOES NOT PROVIDE DOC_QA-SPECIFIC LLM CONFIG FOR NOW. SIMPLY USE DEFAULT)
    config = settings.LLM_CONFIG.get(feature, settings.LLM_CONFIG["default"])
    
    provider = config.get("provider", "deepseek")
    
    # Base defaults from settings
    defaults = {
        "model": config.get("model_name"),
        "temperature": config.get("temperature", 0.3),
    }
    
    # Override with per-call kwargs (e.g. temperature=0)
    defaults.update(kwargs)
    
    if provider == "deepseek":
        return ChatOpenAI(
            api_key=config.get("api_key"),
            base_url=config.get("base_url"),
            **defaults
        )
    else:
        # Default to Gemini
        return ChatGoogleGenerativeAI(
            google_api_key=config.get("api_key"),
            **defaults
        )


# ── Router Node ────────────────────────────────────────────────
ROUTER_SYSTEM_PROMPT = """\
You are a routing assistant. Your ONLY job is to classify the user's intent.

Respond with EXACTLY one of these words (no explanation, no punctuation):
- DOC_QA — ONLY if the user is asking about the software's documentation, how-to guides, \
or app features. Do NOT use this for English language learning questions.
- SCRIPT_EDIT — if the user wants to insert, edit, modify, fix, or \
correct script lines in the database (e.g. "在#100后面加一句", \
"fix the speaker on line 50", "insert a line after #200").
- READER_EDIT — if the user wants to resolve issues with reading materials, \
e.g. edit a paragraph's content, fix translation in the reader, or modify/delete an annotation highlight.
- GENERAL — for English learning questions (idioms, pronunciation, grammar, vocabulary), \
greetings, casual chat, or anything else.

User message:
{message}"""


def router_node(state: AgentState) -> dict:
    """Classify the user's intent and set the `next` field."""
    llm = _get_llm(feature="router", temperature=0)
    
    # Get the last human message
    last_msg = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_msg = msg.content
            break
    
    response = llm.invoke([
        HumanMessage(content=ROUTER_SYSTEM_PROMPT.format(message=last_msg))
    ])
    
    # Parse the routing decision
    decision = response.content.strip().upper()
    
    if "SCRIPT" in decision:
        return {"next": "script_editor"}
    elif "READER" in decision:
        return {"next": "reader_editor"}
    elif "DOC" in decision:
        return {"next": "doc_qa"}
    else:
        return {"next": "general"}


def route_decision(state: AgentState) -> str:
    """Conditional edge: read state['next'] to determine the next node."""
    return state.get("next", "general")


# ── DocQA Node ─────────────────────────────────────────────────
DOC_QA_SYSTEM_PROMPT = """\
You are a helpful documentation assistant for Lingua Workbench, 
a language learning application for studying spoken English from audio sources.

Your role is to answer questions based on the provided documentation context.
Always be helpful, accurate, and concise.

Guidelines:
- Answer in the same language as the user's question (Chinese or English)
- If the context doesn't contain relevant information, say so honestly
- Reference specific features or steps from the documentation
- For how-to questions, provide step-by-step guidance

Documentation Context:
<context>
{context}
</context>"""


def doc_qa_node(state: AgentState) -> dict:
    """Answer questions using DITA documentation (RAG)."""
    from .vector_store import DITAVectorStore
    
    llm = _get_llm(feature="doc_qa")
    
    # Get the last human message
    last_msg = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_msg = msg.content
            break
    
    # Retrieve context from vector store
    vector_store = DITAVectorStore()
    search_results = vector_store.search(query=last_msg, n_results=5)
    
    # Format context
    context = _format_context(search_results) # 将检索到的文档片段格式化为 Markdown 风格的字符串，包含标题、内容和来源信息
    sources = _extract_sources(search_results) # 将检索到的文档片段格式化为列表，包含标题、路径和主题类型
    
    # Generate answer
    response = llm.invoke([
        SystemMessage(content=DOC_QA_SYSTEM_PROMPT.format(context=context)),
        *state["messages"],
    ])
    
    return {
        "messages": [response],
        "context": context,
        "sources": sources,
    }


# ── ScriptEditor Node ─────────────────────────────────────────
SCRIPT_EDITOR_SYSTEM_PROMPT = """\
You are a script editor assistant for Lingua Workbench. You help users \
insert and edit script lines in the database.

Available tools:
1. get_surrounding_lines — Fetch context around a reference line. \
ALWAYS call this FIRST before inserting or editing.
2. insert_script_line — Insert a new line before/after a reference line.
3. edit_script_line — Edit fields of an existing line (speaker, text, etc.)
4. split_script_line — Split a long line: keep first part, move the rest to another chunk.
5. delete_script_line — Delete an existing script line completely.

## CRITICAL RULES (MUST FOLLOW):

### Rule 1: ALWAYS read before writing
Before ANY insert or edit, call get_surrounding_lines to see the current \
content. Never guess what the current text says.

### Rule 2: Partial text edits — preserve the full sentence
When the user wants to change a SPECIFIC WORD or PHRASE in a sentence:
- First read the full original text via get_surrounding_lines.
- Replace ONLY the target word/phrase within the full sentence.
- Pass the COMPLETE modified sentence as the `text` parameter.
- Do NOT pass only the replacement word.

Example:
  User: "把 #2420 的 Ordinary embolism 改成 Coronary embolism"
  WRONG: edit_script_line(line_id=2420, text="Coronary embolism")
  CORRECT: First call get_surrounding_lines(line_id=2420), see the original text \
is "He might have an ordinary embolism in his brain", then call:
  edit_script_line(line_id=2420, text="He might have a coronary embolism in his brain")

### Rule 3: Always sync text_zh when text changes
When you modify the `text` field (English), you MUST also update `text_zh` \
with the corresponding Chinese translation. Generate the translation yourself \
based on the modified English text and surrounding context.

### Rule 4: Speaker Inference & Correction
- If the user says "Change speaker to X", use edit_script_line(speaker="X").
- If the user says "Fix the speaker", infer the correct speaker from context using \
get_surrounding_lines.
- When inserting a line, try to infer the speaker from previous lines if not provided.

### Rule 5: Language & Tone
- Answer in the same language as the user's message.
- After performing the action, confirm what you did with a brief summary \
showing before/after changes.

### Rule 6: Splitting long lines
When the user says a line is too long and asks to move part of it to another chunk:
- First call get_surrounding_lines to read the full text.
- Identify the split point from the user's instruction (e.g. "from the second sentence").
- Call split_script_line with keep_text (first part) and remaining_text (second part).
- The user will specify or imply the target_chunk_id (e.g., "previous chunk" or "next chunk"). \
Carefully determine whether to move the text to the preceding or succeeding chunk based on context. \
Read the exact chunk_id from the context provided by get_surrounding_lines.
- Always generate text_zh translations for both parts."""


# Bind tools to the LLM
SCRIPT_TOOLS = [get_surrounding_lines, insert_script_line, edit_script_line, split_script_line, delete_script_line]


def script_editor_node(state: AgentState) -> dict:
    """Handle script editing requests with tool-calling."""
    llm = _get_llm(feature="script_editor", temperature=0)
    llm_with_tools = llm.bind_tools(SCRIPT_TOOLS)
    
    response = llm_with_tools.invoke([
        SystemMessage(content=SCRIPT_EDITOR_SYSTEM_PROMPT),
        *state["messages"],
    ])
    
    return {"messages": [response]}


# ── ReaderEditor Node ─────────────────────────────────────────
READER_EDITOR_SYSTEM_PROMPT = """\
You are an intelligent reading assistant for Lingua Workbench. You help users \
edit paragraphs, translations, and annotations in their reading materials.

Available tools:
1. get_reader_context — Fetch surrounding paragraphs for context. \
ALWAYS call this FIRST before editing any paragraph or annotation. You can provide \
either `paragraph_id` or `annotation_id`.
2. edit_reader_paragraph — Edit the English text or Chinese translation of a paragraph.
3. edit_reader_annotation — Modify an existing annotation's selected text, note, or type.
4. delete_reader_annotation — Delete a reader annotation.

## CRITICAL RULES (MUST FOLLOW):

### Rule 1: Read before acting
Always call get_reader_context before editing to understand the content. \
If you only have an `annotation_id`, pass it to get_reader_context(annotation_id=...) to fetch the context first. \
Never guess the text.

### Rule 2: Provide feedback
After performing an action, confirm what you did with a brief summary \
showing what was changed based on the user's request. Answer in the same language \
as the user's message.

### Rule 3: Trigger Refresh
If you successfully modify the database using the tools (edit_reader_paragraph, edit_reader_annotation, or delete_reader_annotation), you MUST include the exact string `[REFRESH_READER]` at the very end of your final response so the frontend knows to reload the article. Do NOT include this if no changes were made."""

READER_TOOLS = [get_reader_context, edit_reader_paragraph, edit_reader_annotation, delete_reader_annotation]

def reader_editor_node(state: AgentState) -> dict:
    """Handle reader editing requests with tool-calling."""
    llm = _get_llm(feature="reader_editor", temperature=0)
    llm_with_tools = llm.bind_tools(READER_TOOLS)
    
    response = llm_with_tools.invoke([
        SystemMessage(content=READER_EDITOR_SYSTEM_PROMPT),
        *state["messages"],
    ])
    
    return {"messages": [response]}


def should_continue_tools(state: AgentState) -> str:
    """Check if the last message has tool calls; if so, route to tool node."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


# ── General Chat Node ─────────────────────────────────────────
GENERAL_SYSTEM_PROMPT = """\
You are a friendly assistant for Lingua Workbench, a language learning app. \
Respond naturally to greetings, casual questions, and general conversation. \
You also provide clear explanations for English vocabulary, idioms, and grammar. \
When explaining English pronunciation, always refer to the rules and patterns of American spoken English. \
Answer in the same language as the user's message (Chinese or English). \
Keep responses concise and friendly."""


def general_node(state: AgentState) -> dict:
    """Handle general conversation."""
    llm = _get_llm(feature="general", temperature=0.7)
    
    response = llm.invoke([
        SystemMessage(content=GENERAL_SYSTEM_PROMPT),
        *state["messages"],
    ])
    
    return {"messages": [response]}


# ── Utility Functions ──────────────────────────────────────────
def _format_context(search_results: list[dict]) -> str:
    """Format search results into context string."""
    if not search_results:
        return "No relevant documentation found."
    
    parts = []
    for i, result in enumerate(search_results, 1):
        metadata = result.get('metadata', {})
        title = metadata.get('title', 'Unknown')
        section_path = metadata.get('section_path', '')
        content = result.get('content', '')
        
        doc_xml = f'<document index="{i}">\n<source>{section_path or title}</source>\n<content>\n{content}\n</content>\n</document>'
        parts.append(doc_xml)
    
    return "\n\n".join(parts)


def _extract_sources(search_results: list[dict]) -> list[dict]:
    """Extract source information from search results."""
    sources = []
    seen_paths = set()
    
    for result in search_results:
        metadata = result.get('metadata', {})
        file_path = metadata.get('file_path', '')
        
        if file_path and file_path not in seen_paths:
            seen_paths.add(file_path)
            sources.append({
                'title': metadata.get('title', 'Unknown'),
                'path': file_path,
                'topic_type': metadata.get('topic_type', 'topic'),
            })
    
    return sources


# ── Graph Construction ─────────────────────────────────────────
def build_graph() -> StateGraph:
    """Build and compile the multi-agent graph."""
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("router", router_node)
    graph.add_node("doc_qa", doc_qa_node)
    graph.add_node("script_editor", script_editor_node)
    graph.add_node("reader_editor", reader_editor_node)
    graph.add_node("general", general_node)
    graph.add_node("tools", ToolNode(SCRIPT_TOOLS + READER_TOOLS))
    
    # Entry point
    graph.set_entry_point("router")
    
    # Router → conditional edges
    graph.add_conditional_edges(
        "router",
        route_decision,
        {
            "doc_qa": "doc_qa",
            "script_editor": "script_editor",
            "reader_editor": "reader_editor",
            "general": "general",
        }
    )
    
    # DocQA and General → END
    graph.add_edge("doc_qa", END)
    graph.add_edge("general", END)
    
    # ScriptEditor and ReaderEditor → tool loop (ReAct pattern)
    for node_name in ["script_editor", "reader_editor"]:
        graph.add_conditional_edges(
            node_name,
            should_continue_tools,
            {
                "tools": "tools",
                END: END,
            }
        )
    
    # After tool execution → route back to the agent that called the tool. 
    # But wait, ToolNode default edge goes back to the calling node? 
    # In basic ToolNode, you might need to use standard edges, but LangGraph natively 
    # requires explicit routing back. Let's write a simple router for going back from tools.
    def tools_condition_back(state: AgentState) -> str:
        # Check messages to see which agent made the tool_calls
        last_msg = state["messages"][-2] # -1 is ToolMessage, -2 is AIMessage with tool_calls
        # A simple hack is to rely on tools route_decision, or better, we can just look 
        # at state['next'] which route_decision sets. So we route back to state['next']!
        return state.get("next", "general")

    graph.add_conditional_edges("tools", tools_condition_back)
    
    return graph.compile()


# Singleton compiled graph
app = build_graph()
