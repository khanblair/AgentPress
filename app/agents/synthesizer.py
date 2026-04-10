"""
app/agents/synthesizer.py — Agent 3: The Content Synthesizer
Skill: Narrative writing, document drafting
"""

import json
from app.agents.state import AgentState
from app.agents.client import chat
from app.agents.messenger import post_message
from app.core.config import settings
from app.core.logger import setup_logger

log = setup_logger("synthesizer")

SYSTEM_PROMPT = """You are the Content Synthesizer for AgentPress, an autonomous document pipeline.
Your role is pure language generation — turning research data into polished document text.
You write in a professional, concise, brand-neutral tone.
You structure output with clear ## section headings.
Never apply visual formatting, colors, or styles — that is handled by the Designer."""


def run_synthesizer(state: AgentState) -> AgentState:
    log.info("Synthesizer: Starting content drafting phase.")
    job_id = state.get("job_id", "")
    post_message(job_id, "synthesizer", "✍️ Got it @researcher. Drafting document content from your research brief...")

    document_spec = state.get("document_spec", "")
    task_plan     = state.get("task_plan", [])
    raw_research  = state.get("raw_research", "")
    output_format = state.get("output_format", "docx")

    xlsx_instructions = """
- Output ONLY pipe-delimited tables. No prose, no descriptions, no markdown bold.
- Each ## heading starts a new sheet tab.
- The first row after the heading MUST be the column headers.
- Every subsequent row is a data row with the same number of columns.
- Use plain text only — no ** bold **, no * italic *, no backticks.
- Example format:

## Task Tracker
ID | Task Name | Owner | Priority | Status | Due Date
T001 | Market Research | Marketing | High | In Progress | 2025-06-01
T002 | Design Mockups | Design | Medium | Not Started | 2025-06-15

## Budget Summary
Category | Allocated | Spent | Remaining | Notes
Marketing | $50,000 | $12,000 | $38,000 | Q2 campaigns
Engineering | $120,000 | $45,000 | $75,000 | Salaries only""" if output_format == "xlsx" else ""

    format_instructions = {
        "pptx": "- Write each slide as '## Slide N: [Title]' followed by 4-6 bullet points.",
        "docx": "- Write each section as '## Section Title' followed by paragraphs and bullet points (- item).",
        "pdf":  "- Write each section as '## Section Title' followed by paragraphs and bullet points (- item).",
        "xlsx": xlsx_instructions,
    }.get(output_format, "")

    drafting_prompt = f"""Write the complete document content based on the spec and research below.

DOCUMENT SPEC:
{document_spec}

OUTPUT FORMAT: {output_format.upper()}

TASK PLAN (write each section in order):
{json.dumps(task_plan, indent=2)}

VALIDATED RESEARCH DATA:
{raw_research}

INSTRUCTIONS:
- Follow the task plan exactly, one section per ## heading.
- Use ONLY the validated data — do not invent facts.
{format_instructions}
- Keep it concise."""

    log.debug(f"Synthesizer: Calling {settings.MODEL}.")
    draft_text = chat(SYSTEM_PROMPT, drafting_prompt, temperature=0.4, max_tokens=1024)
    if not draft_text:
        raise ValueError("Synthesizer returned empty content.")
    log.info(f"Synthesizer: draft_text generated ({len(draft_text)} chars).")
    log.debug(f"Synthesizer: draft preview → {draft_text[:400]}...")
    post_message(job_id, "synthesizer", f"✅ Draft complete — {len(draft_text)} chars. @designer please format this into a {output_format.upper()} with brand styling.", "success")

    return {**state, "draft_text": draft_text}
