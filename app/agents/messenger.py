"""
app/agents/messenger.py — Shared inter-agent message bus.

Two channels:
1. Per-job thread: post_message(job_id, ...) — pipeline activity per run
2. Global room: post_global(agent, content) — always-on agent chat room
"""

from datetime import datetime, timezone
from typing import Dict, List

_messages: Dict[str, List[dict]] = {}
_global_room: List[dict] = []
_msg_counter = 0

AGENT_META = {
    "orchestrator":  {"label": "Orchestrator",  "color": "#cdbdff", "emoji": "🧠"},
    "researcher":    {"label": "Researcher",     "color": "#44ddc1", "emoji": "🔍"},
    "synthesizer":   {"label": "Synthesizer",    "color": "#93c5fd", "emoji": "✍️"},
    "designer":      {"label": "Designer",       "color": "#f9a8d4", "emoji": "🎨"},
    "inspector":     {"label": "Inspector",      "color": "#fbbf24", "emoji": "🔬"},
    "meta_engineer": {"label": "Meta-Engineer",  "color": "#f87171", "emoji": "🧬"},
    "system":        {"label": "System",         "color": "#948da2", "emoji": "⚙️"},
    "user":          {"label": "You",            "color": "#e2e8f0", "emoji": "👤"},
}


def _make_msg(agent: str, content: str, msg_type: str, job_id: str = None) -> dict:
    global _msg_counter
    _msg_counter += 1
    meta = AGENT_META.get(agent, AGENT_META["system"])
    return {
        "id": _msg_counter,
        "agent": agent,
        "label": meta["label"],
        "color": meta["color"],
        "emoji": meta["emoji"],
        "content": content,
        "type": msg_type,
        "job_id": job_id,
        "ts": datetime.now(timezone.utc).isoformat(),
    }


def post_message(job_id: str, agent: str, content: str, msg_type: str = "info") -> None:
    """Post to a job-specific thread AND the global room."""
    if not job_id:
        return
    msg = _make_msg(agent, content, msg_type, job_id)
    if job_id not in _messages:
        _messages[job_id] = []
    _messages[job_id].append(msg)
    # Also mirror to global room
    _global_room.append(msg)


def post_global(agent: str, content: str, msg_type: str = "info") -> None:
    """Post directly to the global room (not tied to any job)."""
    _global_room.append(_make_msg(agent, content, msg_type))


def get_messages(job_id: str) -> List[dict]:
    return _messages.get(job_id, [])


def get_global_messages(since_id: int = 0) -> List[dict]:
    return [m for m in _global_room if m["id"] > since_id]


def clear_messages(job_id: str) -> None:
    _messages.pop(job_id, None)
