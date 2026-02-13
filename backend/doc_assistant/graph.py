"""
LangGraph Multi-Agent Graph

Defines the Supervisor-Worker graph:
  Router → DocQA Agent / ScriptEditor Agent / General Chat
"""
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from .state import AgentState
from .tools import get_surrounding_lines, insert_script_line, edit_script_line


from django.conf import settings
from langchain_openai import ChatOpenAI

# ── LLM Instances ──────────────────────────────────────────────
def _get_llm(**kwargs):
    """Create an LLM instance based on settings.LLM_CONFIG."""
    config = settings.LLM_CONFIG
    provider = config.get("provider", "gemini")
    
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
- DOC_QA — if the user is asking about documentation, how-to guides, \
app features, or anything about the Lingua Workbench application.
- SCRIPT_EDIT — if the user wants to insert, edit, modify, fix, or \
correct script lines in the database (e.g. "在#100后面加一句", \
"fix the speaker on line 50", "insert a line after #200").
- GENERAL — for greetings, casual chat, or anything else.

User message:
{message}"""


def router_node(state: AgentState) -> dict:
    """Classify the user's intent and set the `next` field."""
    llm = _get_llm(temperature=0)
    
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
{context}"""


def doc_qa_node(state: AgentState) -> dict:
    """Answer questions using DITA documentation (RAG)."""
    from .vector_store import DITAVectorStore
    
    llm = _get_llm()
    
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
    context = _format_context(search_results)
    sources = _extract_sources(search_results)
    
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
showing before/after changes."""


# Bind tools to the LLM
SCRIPT_TOOLS = [get_surrounding_lines, insert_script_line, edit_script_line]


def script_editor_node(state: AgentState) -> dict:
    """Handle script editing requests with tool-calling."""
    llm = _get_llm(temperature=0)
    llm_with_tools = llm.bind_tools(SCRIPT_TOOLS)
    
    response = llm_with_tools.invoke([
        SystemMessage(content=SCRIPT_EDITOR_SYSTEM_PROMPT),
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
Answer in the same language as the user's message (Chinese or English). \
Keep responses concise and friendly."""


def general_node(state: AgentState) -> dict:
    """Handle general conversation."""
    llm = _get_llm(temperature=0.7)
    
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
        parts.append(f"[Document {i}: {section_path or title}]\n{content}")
    
    return "\n\n---\n\n".join(parts)


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
    graph.add_node("general", general_node)
    graph.add_node("tools", ToolNode(SCRIPT_TOOLS))
    
    # Entry point
    graph.set_entry_point("router")
    
    # Router → conditional edges
    graph.add_conditional_edges(
        "router",
        route_decision,
        {
            "doc_qa": "doc_qa",
            "script_editor": "script_editor",
            "general": "general",
        }
    )
    
    # DocQA and General → END
    graph.add_edge("doc_qa", END)
    graph.add_edge("general", END)
    
    # ScriptEditor → tool loop (ReAct pattern)
    graph.add_conditional_edges(
        "script_editor",
        should_continue_tools,
        {
            "tools": "tools",
            END: END,
        }
    )
    
    # After tool execution → back to ScriptEditor for next reasoning step
    graph.add_edge("tools", "script_editor")
    
    return graph.compile()


# Singleton compiled graph
app = build_graph()
