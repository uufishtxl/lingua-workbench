"""
Vector Store Management for DITA RAG

Uses ChromaDB with Gemini embeddings for semantic search.
"""
from pathlib import Path
from typing import Optional
import chromadb
from chromadb.config import Settings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from django.conf import settings
import os

from .dita_parser import DITAChunk


class DITAVectorStore:
    """
    Manages the Chroma vector store for DITA documentation.
    
    Key Responsibilities:
    1. Initialize/load the vector store
    2. Add chunks with embeddings
    3. Search with audience filtering
    """
    
    COLLECTION_NAME = "dita_docs"
    
    def __init__(self, persist_directory: Optional[Path] = None):
        """
        Initialize the vector store.
        
        Args:
            persist_directory: Where to store the Chroma DB. 
                             Defaults to backend/doc_assistant/chroma_db
        """
        if persist_directory is None:
            persist_directory = Path(__file__).parent / "chroma_db"
        
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize Chroma client with persistence
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False),
        )
        
        # Initialize Gemini embeddings
        # Note: Model name needs "models/" prefix for LangChain
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"description": "DITA documentation chunks for RAG"}
        )
    
    def add_chunks(self, chunks: list[DITAChunk], batch_size: int = 50) -> int:
        """
        Add chunks to the vector store with embeddings.
        
        Args:
            chunks: List of DITAChunk objects
            batch_size: Process in batches to respect API rate limits
            
        Returns:
            Number of chunks added
        """
        total_added = 0
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            # Prepare data for Chroma
            ids = [chunk.id for chunk in batch]
            documents = [chunk.content for chunk in batch]
            metadatas = [chunk.to_metadata() for chunk in batch]
            
            # Generate embeddings
            embeddings = self.embeddings.embed_documents(documents)
            
            # Upsert to collection (handles duplicates)
            self.collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings,
            )
            
            total_added += len(batch)
            print(f"Added {total_added}/{len(chunks)} chunks...")
        
        return total_added
    
    def search(
        self,
        query: str,
        audience: str = 'all',
        n_results: int = 5,
    ) -> list[dict]:
        """
        Search for relevant chunks.
        
        Args:
            query: User's question
            audience: Filter by audience ('user', 'developer', 'all')
            n_results: Number of results to return
            
        Returns:
            List of matching documents with metadata
        """
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)
        
        # Build where clause for audience filtering
        # 'all' audience should match everything
        # 'user' should see 'all' and 'user' content
        # 'developer' should see 'all', 'user', and 'developer' content
        where_filter = None
        if audience == 'user':
            where_filter = {
                "$or": [
                    {"audience": "all"},
                    {"audience": "user"},
                ]
            }
        # Developer sees everything, no filter needed
        
        # Query the collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )
        
        # Format results
        formatted = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                formatted.append({
                    'content': doc,
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else None,
                })
        
        return formatted
    
    def get_stats(self) -> dict:
        """Get collection statistics."""
        return {
            'total_chunks': self.collection.count(),
            'persist_directory': str(self.persist_directory),
        }
    
    def clear(self):
        """Clear all data from the collection."""
        self.client.delete_collection(self.COLLECTION_NAME)
        self.collection = self.client.create_collection(
            name=self.COLLECTION_NAME,
            metadata={"description": "DITA documentation chunks for RAG"}
        )
