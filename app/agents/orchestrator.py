"""
app/agents/orchestrator.py — Agent 1: Lead Orchestrator
Model: openai/gpt-oss-120b:free (via OpenRouter)

Responsibilities:
 - Load brand.md + user.md from knowledge base
 - Load compressed session memory
 - Run Superpowers brainstorm → finalise document_spec
 - Run Superpowers writing_plans → produce task_plan list
 - Set output_format from user prompt
"""

import uuid
from openai import OpenAI

from app.agents.state import AgentState
from app.core.config import settings
from app.core.logger import setup_logger
from app.memory.session import SessionMemory
from app.tools.superpowers.brainstorm import build_brainstorm_prompt
from app.tools.superpowers.writing_plans import build_task_plan

log = setup_logger("orchestrator")

client = OpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url=settings.OPENROUTER_BASE_URL,
)


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

    # 1. Load knowledge base context
    brand_context = _load_knowledge("app/knowledge_base/brand.md")
    user_context = _load_knowledge("app/knowledge_base/user.md")

    # 2. Load compressed session memory
    memory = SessionMemory(session_id)
    session_context = memory.retrieve_relevant(user_prompt)

    # 3. Determine output format from prompt keywords
    fmt = "docx"
    for keyword, ftype in [
        ("pptx", "pptx"), ("slide", "pptx"), ("presentation", "pptx"),
        ("excel", "xlsx"), ("spreadsheet", "xlsx"), ("csv", "xlsx"),
        ("pdf", "pdf"),
    ]:
        if keyword in user_prompt.lower():
            fmt = ftype
            break

    # 4. Brainstorm → document_spec
    brainstorm_prompt = build_brainstorm_prompt(
        user_prompt=user_prompt,
        brand_context=brand_context,
        user_context=user_context,
        session_context=session_context,
    )
    log.debug(f"Orchestrator: Calling {settings.ORCHESTRATOR_MODEL} for brainstorm.")
    spec_response = client.chat.completions.create(
        model=settings.ORCHESTRATOR_MODEL,
        messages=[{"role": "user", "content": brainstorm_prompt}],
        temperature=0.3,
    )
    document_spec = spec_response.choices[0].message.content.strip()
    log.info("Orchestrator: document_spec finalised.")

    # 5. Writing plan → task_plan
    plan_prompt = build_task_plan(document_spec=document_spec, output_format=fmt)
    plan_response = client.chat.completions.create(
        model=settings.ORCHESTRATOR_MODEL,
        messages=[{"role": "user", "content": plan_prompt}],
        temperature=0.2,
    )
    plan_raw = plan_response.choices[0].message.content.strip()
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
