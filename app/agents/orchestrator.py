"""
app/agents/orchestrator.py — Agent 1: Lead Orchestrator
Skill: Planning, brainstorming, task decomposition
"""

import uuid
import re
from app.agents.state import AgentState
from app.agents.client import chat
from app.agents.messenger import post_message
from app.core.config import settings
from app.core.logger import setup_logger
from app.memory.session import SessionMemory
from app.tools.superpowers.brainstorm import build_brainstorm_prompt
from app.tools.superpowers.writing_plans import build_task_plan

log = setup_logger("orchestrator")

SYSTEM_PROMPT = """You are the Lead Orchestrator for AgentPress, an autonomous document pipeline.
Your role is strategic planning and task decomposition.
You are authoritative, concise, and data-driven.
You produce structured Markdown specifications and numbered task plans.
Never write the document itself — only plan and specify."""


def _load_knowledge(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def _derive_title(prompt: str, spec: str) -> str:
    """
    Derive a clean filename slug from the user prompt or document spec.
    e.g. "Create a Q3 market analysis report" → "q3-market-analysis-report"
    """
    # Try to extract a title from the first line of the spec (often "# Title" or "**Title**")
    for line in spec.splitlines():
        line = line.strip().lstrip("#* ").rstrip("#* ")
        if 4 < len(line) < 80 and not line.startswith(("Document", "Spec", "Overview")):
            source = line
            break
    else:
        # Fall back to the user prompt
        source = prompt

    # Strip common filler words and clean to slug
    slug = source.lower()
    slug = re.sub(r'\b(create|write|make|generate|build|a|an|the|for|of|with|and|to|in|on)\b', ' ', slug)
    slug = re.sub(r'[^a-z0-9\s]', '', slug)
    slug = re.sub(r'\s+', '-', slug.strip())
    slug = slug.strip('-')[:60]  # max 60 chars
    return slug or "document"


def run_orchestrator(state: AgentState) -> AgentState:
    job_id = state.get("job_id", "")
    log.info("Orchestrator: Starting intake & planning phase.")
    post_message(job_id, "orchestrator", f"📋 Received prompt. Detecting output format and loading brand context...")

    session_id = state.get("session_id") or str(uuid.uuid4())
    user_prompt = state.get("user_prompt", "")

    brand_context = _load_knowledge("app/knowledge_base/brand.md")
    user_context  = _load_knowledge("app/knowledge_base/user.md")
    memory        = SessionMemory(session_id)
    session_context = memory.retrieve_relevant(user_prompt)

    # Detect output format
    fmt = "docx"
    for keyword, ftype in [
        ("pptx", "pptx"), ("slide", "pptx"), ("presentation", "pptx"),
        ("excel", "xlsx"), ("spreadsheet", "xlsx"), ("csv", "xlsx"),
        ("pdf", "pdf"),
    ]:
        if keyword in user_prompt.lower():
            fmt = ftype
            break

    # Brainstorm → document_spec
    brainstorm_prompt = build_brainstorm_prompt(
        user_prompt=user_prompt,
        brand_context=brand_context,
        user_context=user_context,
        session_context=session_context,
    )
    log.debug(f"Orchestrator: Calling {settings.MODEL} for brainstorm.")
    document_spec = chat(SYSTEM_PROMPT, brainstorm_prompt, temperature=0.3, max_tokens=512)
    log.info("Orchestrator: document_spec finalised.")
    log.debug(f"Orchestrator: document_spec preview → {document_spec[:200]}...")
    post_message(job_id, "orchestrator", f"✅ Document spec finalised. Output format: **{fmt.upper()}**", "success")

    # Derive a human-readable filename slug
    document_title = _derive_title(user_prompt, document_spec)
    log.info(f"Orchestrator: document_title → {document_title}")


    # Writing plan → task_plan
    plan_prompt = build_task_plan(document_spec=document_spec, output_format=fmt)
    plan_raw = chat(SYSTEM_PROMPT, plan_prompt, temperature=0.2, max_tokens=256)
    task_plan = [
        line.lstrip("0123456789.-) ").strip()
        for line in plan_raw.splitlines()
        if line.strip()
    ]
    log.info(f"Orchestrator: task_plan has {len(task_plan)} tasks.")
    for i, task in enumerate(task_plan, 1):
        log.debug(f"  Task {i}: {task}")
    post_message(job_id, "orchestrator", f"📝 Task plan ready — {len(task_plan)} tasks queued. @researcher please gather data for this spec.", "info")

    return {
        **state,
        "session_id": session_id,
        "document_spec": document_spec,
        "document_title": document_title,
        "task_plan": task_plan,
        "output_format": fmt,
        "qa_retry_count": 0,
        "qa_passed": False,
        "evolution_triggered": False,
    }
