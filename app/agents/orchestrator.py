"""
app/agents/orchestrator.py — Agent 1: Lead Orchestrator
Skill: Planning, brainstorming, task decomposition
"""

import uuid
from app.agents.state import AgentState
from app.agents.client import chat
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


def run_orchestrator(state: AgentState) -> AgentState:
    log.info("Orchestrator: Starting intake & planning phase.")

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

    # Writing plan → task_plan
    plan_prompt = build_task_plan(document_spec=document_spec, output_format=fmt)
    plan_raw = chat(SYSTEM_PROMPT, plan_prompt, temperature=0.2, max_tokens=256)
    task_plan = [
        line.lstrip("0123456789.-) ").strip()
        for line in plan_raw.splitlines()
        if line.strip()
    ]
    log.info(f"Orchestrator: task_plan has {len(task_plan)} tasks.")

    return {
        **state,
        "session_id": session_id,
        "document_spec": document_spec,
        "task_plan": task_plan,
        "output_format": fmt,
        "qa_retry_count": 0,
        "qa_passed": False,
        "evolution_triggered": False,
    }
