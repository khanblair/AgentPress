"""
app/memory/vector_db.py

Minimal ChromaDB wrapper for brand knowledge and session persistence.
"""

import chromadb
from chromadb.config import Settings
from app.core.config import settings
from app.core.logger import setup_logger

log = setup_logger("vector_db")

class VectorDB:
    def __init__(self, path: str = settings.CHROMA_DB_PATH):
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(name="agentpress_memory")

    def add_memory(self, session_id: str, text: str, metadata: dict = None):
        """Add a memory snippet with session_id metadata."""
        meta = metadata or {}
        meta["session_id"] = session_id
        
        self.collection.add(
            documents=[text],
            metadatas=[meta],
            ids=[f"{session_id}_{hash(text)}"]
        )
        log.debug(f"Memory added for session {session_id}")

    def query_memory(self, query: str, session_id: str = None, top_k: int = 3):
        """Query personal or global memory."""
        where_clause = {"session_id": session_id} if session_id else None
        
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_clause
        )
        return results["documents"][0] if results["documents"] else []

# Global instance
vdb = VectorDB()
