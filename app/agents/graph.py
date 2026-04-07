"""
app/agents/graph.py — LangGraph StateGraph: nodes, edges, and fallback loops

Pipeline flow:
  orchestrator → researcher → synthesizer → designer → inspector
                                                           │
                              ┌────── qa_passed? ──────────┤
                              │  No (retry < MAX)          │ Yes
                              ▼                            ▼
                           designer              [evolution_check]
                              │                            │
                   No (max retries hit)           evolution needed?
                              ▼                    No ▼       Yes ▼
                       meta_engineer             END       meta_engineer → END
"""

from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.orchestrator import run_orchestrator
from app.agents.researcher import run_researcher
from app.agents.synthesizer import run_synthesizer
from app.agents.designer import run_designer
from app.agents.inspector import run_inspector
from app.agents.meta_engineer import run_meta_engineer
from app.core.config import settings
from app.core.logger import setup_logger

log = setup_logger("graph")


# ── Conditional edge functions ─────────────────────────────────────────────────

def route_after_inspector(state: AgentState) -> str:
    """Decide where to go after QA inspection."""
    if state.get("qa_passed"):
        log.info("QA passed. Checking if evolution is needed...")
        if state.get("evolution_triggered"):
            return "meta_engineer"
        return END
    retry_count = state.get("qa_retry_count", 0)
    if retry_count >= settings.MAX_QA_RETRIES:
        log.warning(f"Max QA retries ({settings.MAX_QA_RETRIES}) hit — escalating to Meta-Engineer.")
        return "meta_engineer"
    log.info(f"QA failed (retry {retry_count}). Routing back to Designer.")
    return "designer"


def route_after_meta_engineer(state: AgentState) -> str:
    """After Meta-Engineer writes a new skill, end the pipeline."""
    log.info("Meta-Engineer finished. Ending pipeline run.")
    return END


# ── Graph definition ────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("orchestrator", run_orchestrator)
    graph.add_node("researcher", run_researcher)
    graph.add_node("synthesizer", run_synthesizer)
    graph.add_node("designer", run_designer)
    graph.add_node("inspector", run_inspector)
    graph.add_node("meta_engineer", run_meta_engineer)

    # Entry point
    graph.set_entry_point("orchestrator")

    # Linear edges
    graph.add_edge("orchestrator", "researcher")
    graph.add_edge("researcher", "synthesizer")
    graph.add_edge("synthesizer", "designer")
    graph.add_edge("designer", "inspector")

    # Conditional edges
    graph.add_conditional_edges(
        "inspector",
        route_after_inspector,
        {
            "designer": "designer",
            "meta_engineer": "meta_engineer",
            END: END,
        },
    )
    graph.add_conditional_edges(
        "meta_engineer",
        route_after_meta_engineer,
        {END: END},
    )

    return graph


# Compile the runnable graph (used by API routes)
compiled_graph = build_graph().compile()
