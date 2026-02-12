"""
RAG Service for Documentation Assistant

Refactored to use LangGraph multi-agent system.
Orchestrates routing between DocQA, ScriptEditor, and General agents.
"""
from typing import Generator
from pathlib import Path
from langchain_core.messages import HumanMessage, AIMessage
from django.conf import settings

from .graph import app as agent_app
from .vector_store import DITAVectorStore


class DocAssistantService:
    """
    Main service for handling documentation Q&A with multi-agent RAG.
    
    Delegates to LangGraph graph which routes between:
    - DocQA Agent (documentation questions)
    - ScriptEditor Agent (insert/edit script lines)
    - General Agent (casual conversation)
    """
    
    def __init__(self):
        self.app = agent_app
        # Keep vector_store accessible for views that need direct access
        self.vector_store = DITAVectorStore()
    
    def get_answer(self, question: str, audience: str = 'all') -> dict:
        """
        Get a complete answer (non-streaming).
        
        Args:
            question: User's question
            audience: 'user' or 'developer' (used for DocQA filtering)
            
        Returns:
            Dict with answer and sources
        """
        # Invoke the graph
        result = self.app.invoke({
            "messages": [HumanMessage(content=question)],
            "next": "",
            "context": "",
            "sources": [],
        })
        
        # Extract the final AI message
        last_ai_msg = ""
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and msg.content:
                last_ai_msg = msg.content
                break
        
        return {
            "answer": last_ai_msg,
            "sources": result.get("sources", []),
        }
    
    def stream_answer(
        self,
        question: str,
        audience: str = 'all',
    ) -> Generator[str, None, None]:
        """
        Stream the answer token by token.
        
        Uses LangGraph's stream_mode="messages" to yield individual tokens
        from whichever agent is responding.
        
        Args:
            question: User's question
            audience: 'user' or 'developer'
            
        Yields:
            String tokens as they are generated
        """
        initial_state = {
            "messages": [HumanMessage(content=question)],
            "next": "",
            "context": "",
            "sources": [],
        }
        
        for msg, metadata in self.app.stream(
            initial_state,
            stream_mode="messages",
        ):
            # Only yield content tokens from AI messages (not tool calls)
            if (
                isinstance(msg, AIMessage)
                and msg.content
                and not msg.tool_calls
            ):
                yield msg.content
    
    def get_sources_after_stream(self, question: str, audience: str = 'all') -> list[dict]:
        """
        Get sources after streaming is complete.
        
        Since streaming doesn't easily return sources inline,
        this re-runs a quick vector search to get sources.
        Only relevant for DOC_QA queries.
        """
        search_results = self.vector_store.search(
            query=question,
            audience=audience,
            n_results=5,
        )
        return self._extract_sources(search_results)
    
    def _extract_sources(self, search_results: list[dict]) -> list[dict]:
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


def build_index(dita_root: Path, clear_existing: bool = False) -> dict:
    """
    Build or rebuild the vector index from DITA files.
    
    Args:
        dita_root: Path to the DITA documentation root
        clear_existing: Whether to clear existing index first
        
    Returns:
        Statistics about the indexing
    """
    from .dita_parser import DITAChunker
    
    # Initialize
    chunker = DITAChunker(dita_root)
    vector_store = DITAVectorStore()
    
    # Optionally clear existing data
    if clear_existing:
        vector_store.clear()
        print("Cleared existing index.")
    
    # Parse DITA files
    print(f"Parsing DITA files from {dita_root}...")
    chunks = chunker.parse_all_files()
    print(f"Found {len(chunks)} chunks from DITA files.")
    
    # Add to vector store
    print("Adding chunks to vector store...")
    added = vector_store.add_chunks(chunks)
    
    # Get final stats
    stats = vector_store.get_stats()
    stats['chunks_processed'] = len(chunks)
    stats['chunks_added'] = added
    
    return stats
