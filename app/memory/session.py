"""
app/memory/session.py

Session memory management using SQLite and VectorDB.
Handles context compression and retrieval.
"""

from app.memory.vector_db import vdb
from app.core.logger import setup_logger

log = setup_logger("session")

class SessionMemory:
    def __init__(self, session_id: str):
        self.session_id = session_id

    def add_interaction(self, role: str, content: str):
        """Store interaction in vector DB for long-term recall."""
        text = f"{role.upper()}: {content}"
        vdb.add_memory(self.session_id, text)

    def retrieve_relevant(self, query: str, top_k: int = 5) -> str:
        """Retrieve relevant past interactions from this session."""
        memories = vdb.query_memory(query, session_id=self.session_id, top_k=top_k)
        if not memories:
            return ""
        
        return "\n---\n".join(memories)

    def compress_context(self, conversation_history: list) -> str:
        """
        Simulated context compression. 
        In production, this would use an LLM to summarise past turns.
        """
        if not conversation_history:
            return ""
        
        # Simple summary for MVP
        last_turn = conversation_history[-1]
        summary = f"Summary of session {self.session_id}: User requested {last_turn.get('content')[:100]}..."
        return summary
