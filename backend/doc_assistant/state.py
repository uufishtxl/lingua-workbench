"""
Agent State Definition for Multi-Agent System

Shared state that flows through the LangGraph nodes.
"""
from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    Shared state for the multi-agent graph.
    
    Fields:
        messages: Conversation history (auto-merged via add_messages reducer)
        next: Routing decision from the router node
        context: Retrieved RAG context (for DocQA)
        sources: Source documents from vector search
    """
    messages: Annotated[list, add_messages]
    next: Literal["doc_qa", "script_editor", "general"]
    context: str
    sources: list[dict]
