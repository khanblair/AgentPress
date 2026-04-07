"""
app/agents/inspector.py — Agent 5: Compliance Inspector
Model: qwen/qwen3-235b-a22b:free (via OpenRouter)

Responsibilities:
 - Stage 1: Factual accuracy — cross-check draft_text against raw_research
 - Stage 2: Brand compliance — verify formatting_code applied brand.md rules
 - Set qa_passed True/False + write qa_report
 - Use systematic-debugging Superpowers pattern on failures
"""

from openai import OpenAI
from pathlib import Path

from app.agents.state import AgentState
from app.core.config import settings
from app.core.logger import setup_logger
from app.tools.superpowers.debug import build_debug_prompt

log = setup_logger("inspector")

client = OpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url=settings.OPENROUTER_BASE_URL,
)


def _load_brand() -> str:
    try:
        with open("app/knowledge_base/brand.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


PASS_SIGNAL = "QA_VERDICT: PASS"
FAIL_SIGNAL = "QA_VERDICT: FAIL"


def run_inspector(state: AgentState) -> AgentState:
    log.info("Inspector: Starting two-stage QA review.")

    draft_text = state.get("draft_text", "")
    raw_research = state.get("raw_research", "")
    formatting_code = state.get("formatting_code", "")
    tdd_passed = state.get("tdd_passed", False)
    output_format = state.get("output_format", "docx")
    brand_guidelines = _load_brand()
    retry_count = state.get("qa_retry_count", 0)

    # ── Stage 1: Factual accuracy ──────────────────────────────────────
    factual_prompt = f"""You are a strict QA compliance inspector.

TASK: Stage 1 — Factual Accuracy Review

VALIDATED RESEARCH DATA (ground truth):
{raw_research[:2000]}

DRAFT TEXT TO REVIEW:
{draft_text[:2000]}

INSTRUCTIONS:
- Check every factual claim in the draft against the research data.
- Flag any hallucinations, unsupported statistics, or invented details.
- Be specific about line numbers or sections.
- End your report with exactly one of these lines:
  {PASS_SIGNAL}
  {FAIL_SIGNAL}

Write your Stage 1 review:"""

    log.debug("Inspector: Stage 1 — factual review.")
    r1 = client.chat.completions.create(
        model=settings.INSPECTOR_MODEL,
        messages=[{"role": "user", "content": factual_prompt}],
        temperature=0.1,
    )
    stage1_report = r1.choices[0].message.content.strip()
    stage1_passed = PASS_SIGNAL in stage1_report

    # ── Stage 2: Brand compliance ──────────────────────────────────────
    brand_prompt = f"""You are a strict QA compliance inspector.

TASK: Stage 2 — Brand Compliance Review

BRAND GUIDELINES:
{brand_guidelines or "No brand guidelines provided."}

FORMATTING CODE WRITTEN BY DESIGNER:
```python
{formatting_code[:2000]}
```

FILE OUTPUT EXISTS: {"Yes" if tdd_passed else "No — script failed to execute"}
OUTPUT FORMAT: {output_format.upper()}

INSTRUCTIONS:
- Verify the code applies the correct hex colors from brand guidelines.
- Verify fonts and layout match brand spec.
- Verify the output file would be correctly generated.
- Flag any deviations from brand rules.
- End your report with exactly one of these lines:
  {PASS_SIGNAL}
  {FAIL_SIGNAL}

Write your Stage 2 review:"""

    log.debug("Inspector: Stage 2 — brand compliance review.")
    r2 = client.chat.completions.create(
        model=settings.INSPECTOR_MODEL,
        messages=[{"role": "user", "content": brand_prompt}],
        temperature=0.1,
    )
    stage2_report = r2.choices[0].message.content.strip()
    stage2_passed = PASS_SIGNAL in stage2_report

    qa_passed = stage1_passed and stage2_passed and tdd_passed
    qa_report = f"## Stage 1: Factual Accuracy\n{stage1_report}\n\n## Stage 2: Brand Compliance\n{stage2_report}"

    # ── If failed: apply systematic-debugging to trace root cause ─────
    error_log = state.get("error_log", "")
    if not qa_passed:
        debug_prompt = build_debug_prompt(
            error_description=f"QA FAILED on retry {retry_count}",
            stage1_report=stage1_report,
            stage2_report=stage2_report,
            formatting_code=formatting_code,
        )
        r3 = client.chat.completions.create(
            model=settings.INSPECTOR_MODEL,
            messages=[{"role": "user", "content": debug_prompt}],
            temperature=0.1,
        )
        debug_report = r3.choices[0].message.content.strip()
        error_log = debug_report
        log.warning(f"Inspector: QA FAILED (retry {retry_count}). Root cause traced.")
    else:
        log.info(f"Inspector: QA PASSED on attempt {retry_count + 1}.")

    return {
        **state,
        "qa_passed": qa_passed,
        "qa_report": qa_report,
        "qa_retry_count": retry_count + (0 if qa_passed else 1),
        "error_log": error_log,
    }
