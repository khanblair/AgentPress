"""
app/agents/state.py — Shared AgentState TypedDict (Redux-style pipeline state)

This is the single source of truth for all data flowing through the LangGraph.
Every agent reads from and writes to specific keys in this dict.
"""

from typing import TypedDict, Optional, List


class AgentState(TypedDict, total=False):
    # ── Input ──────────────────────────────────────────────────────────
    user_prompt: str                  # Raw user request
    session_id: str                   # Unique ID for this pipeline run
    job_id: str                       # AsyncIO job reference (REST polling)

    # ── Agent 1: Orchestrator outputs ─────────────────────────────────
    document_spec: str                # Finalised document specification
    document_title: str               # Human-readable filename slug (e.g. "q3-market-analysis")
    task_plan: List[str]              # Ordered list of isolated sub-tasks
    output_format: str                # "pptx" | "docx" | "xlsx" | "pdf"

    # ── Agent 2: Researcher outputs ────────────────────────────────────
    raw_research: str                 # Concatenated validated data dump
    rag_sources: List[str]            # Chunk IDs from RAGFlow (for QA cross-check)
    web_sources: List[str]            # URLs scraped from Agent Reach tools

    # ── Agent 3: Synthesizer outputs ───────────────────────────────────
    draft_text: str                   # Raw narrative draft (pre-branding)

    # ── Agent 4: Designer outputs ──────────────────────────────────────
    formatted_file_path: str          # Absolute path to the compiled output file
    formatting_code: str              # The python-docx / python-pptx script written
    tdd_passed: bool                  # Did RED→GREEN→REFACTOR cycle pass?

    # ── Agent 5: Inspector outputs ─────────────────────────────────────
    qa_passed: bool                   # Final QA approval
    qa_report: str                    # Human-readable compliance report
    qa_retry_count: int               # Number of QA retry loops so far
    error_log: str                    # Error detail for debugging

    # ── Agent 6: Meta-Engineer outputs ────────────────────────────────
    evolution_triggered: bool         # Was self-improvement loop activated?
    new_skill_path: str               # Path to newly generated tool script
    evolution_changelog: str          # Markdown changelog entry

    # ── Human Correction (POST /submit-correction) ────────────────────
    correction_original: str          # Original AI-generated content
    correction_edited: str            # Human-edited version
    correction_delta: str             # Diff summary from delta_parser
