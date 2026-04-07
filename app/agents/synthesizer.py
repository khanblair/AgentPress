"""
app/agents/synthesizer.py — Agent 3: The Content Synthesizer
Model: meta-llama/llama-3.2-3b-instruct:free (via OpenRouter)

Responsibilities:
 - Pure language generation: take task_plan + raw_research → draft_text
 - Focus on narrative structure, logical flow, and language quality
 - No tool calls, no brand formatting — that is Agent 4's job
"""

import json
from openai import OpenAI

from app.agents.state import AgentState
from app.core.config import settings
from app.core.logger import setup_logger

log = setup_logger("synthesizer")

client = OpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url=settings.OPENROUTER_BASE_URL,
)


def run_synthesizer(state: AgentState) -> AgentState:
    log.info("Synthesizer: Starting content drafting phase.")

    document_spec = state.get("document_spec", "")
    task_plan = state.get("task_plan", [])
    raw_research = state.get("raw_research", "")
    output_format = state.get("output_format", "docx")

    drafting_prompt = f"""You are a professional content writer creating enterprise documents.

DOCUMENT SPEC:
{document_spec}

OUTPUT FORMAT: {output_format.upper()}

TASK PLAN (write each section in order):
{json.dumps(task_plan, indent=2)}

VALIDATED RESEARCH DATA:
{raw_research}

INSTRUCTIONS:
- Write the complete document text following the task plan exactly.
- Use ONLY the validated data provided — do not invent facts.
- Structure the output with clear section headings (## for each task plan item).
- Write in a professional, concise, brand-neutral tone.
- Do NOT apply any visual formatting, colors, or styles — that is handled separately.
- For presentations (pptx), write each slide as: "## Slide N: [Title]" followed by bullet points.

Begin writing now:"""

    log.debug(f"Synthesizer: Calling {settings.SYNTHESIZER_MODEL}.")
    response = client.chat.completions.create(
        model=settings.SYNTHESIZER_MODEL,
        messages=[{"role": "user", "content": drafting_prompt}],
        temperature=0.4,
        max_tokens=4096,
    )
    draft_text = response.choices[0].message.content.strip()
    log.info(f"Synthesizer: draft_text generated ({len(draft_text)} chars).")

    return {
        **state,
        "draft_text": draft_text,
    }
