"""
RAG Service for Documentation Assistant

Orchestrates the retrieval and generation pipeline with streaming support.
"""
from typing import Generator
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from django.conf import settings
import os

from .vector_store import DITAVectorStore


# System prompt for the documentation assistant
SYSTEM_PROMPT = """You are a helpful documentation assistant for Lingua Workbench, 
a language learning application for studying spoken English from audio sources.

Your role is to answer questions based on the provided documentation context.
Always be helpful, accurate, and concise.

Guidelines:
- Answer in the same language as the user's question (Chinese or English)
- If the context doesn't contain relevant information, say so honestly
- Reference specific features or steps from the documentation
- For how-to questions, provide step-by-step guidance

Documentation Context:
{context}

User's Question: {question}"""


class DocAssistantService:
    """
    Main service for handling documentation Q&A with RAG.
    """
    
    def __init__(self):
        self.vector_store = DITAVectorStore()
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.3,
            streaming=True,
        )
        
        self.prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)
        self.chain = self.prompt | self.llm | StrOutputParser()
    
    def get_answer(self, question: str, audience: str = 'all') -> dict:
        """
        Get a complete answer (non-streaming).
        
        Args:
            question: User's question
            audience: 'user' or 'developer'
            
        Returns:
            Dict with answer and sources
        """
        # Retrieve relevant context
        search_results = self.vector_store.search(
            query=question,
            audience=audience,
            n_results=5,
        )
        
        # Format context from search results
        context = self._format_context(search_results)
        
        # Generate answer
        answer = self.chain.invoke({
            "context": context,
            "question": question,
        })
        
        # Extract sources
        sources = self._extract_sources(search_results)
        
        return {
            "answer": answer,
            "sources": sources,
        }
    
    def stream_answer(
        self,
        question: str,
        audience: str = 'all',
    ) -> Generator[str, None, dict]:
        """
        Stream the answer token by token for typewriter effect.
        
        Args:
            question: User's question
            audience: 'user' or 'developer'
            
        Yields:
            String tokens as they are generated
            
        Returns:
            Final dict with sources (after iteration complete)
        """
        # Retrieve relevant context
        search_results = self.vector_store.search(
            query=question,
            audience=audience,
            n_results=5,
        )
        
        # Format context
        context = self._format_context(search_results)
        
        # Stream the response
        for chunk in self.chain.stream({
            "context": context,
            "question": question,
        }):
            yield chunk
        
        # Return sources info at the end
        return {
            "sources": self._extract_sources(search_results),
        }
    
    def _format_context(self, search_results: list[dict]) -> str:
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
