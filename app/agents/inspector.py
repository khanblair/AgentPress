"""
app/agents/inspector.py — Agent 5: Compliance Inspector
Skill: Two-stage QA — factual accuracy + brand compliance
"""

from app.agents.state import AgentState
from app.agents.client import chat
from app.agents.messenger import post_message
from app.core.config import settings
from app.core.logger import setup_logger
from app.tools.superpowers.debug import build_debug_prompt

log = setup_logger("inspector")

SYSTEM_PROMPT = """You are the Compliance Inspector for AgentPress, an autonomous document pipeline.
Your role is strict quality assurance — factual accuracy and brand compliance.
You are methodical, precise, and uncompromising.
You always end your review with exactly one of: QA_VERDICT: PASS or QA_VERDICT: FAIL"""

PASS_SIGNAL = "QA_VERDICT: PASS"
FAIL_SIGNAL = "QA_VERDICT: FAIL"


def _load_brand() -> str:
    try:
        with open("app/knowledge_base/brand.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def run_inspector(state: AgentState) -> AgentState:
    log.info("Inspector: Starting two-stage QA review.")
    job_id = state.get("job_id", "")
    post_message(job_id, "inspector", "🔬 Received @designer. Running 2-stage QA — factual accuracy then brand compliance...")

    draft_text      = state.get("draft_text", "")
    raw_research    = state.get("raw_research", "")
    formatting_code = state.get("formatting_code", "")
    tdd_passed      = state.get("tdd_passed", False)
    output_format   = state.get("output_format", "docx")
    brand_guidelines = _load_brand()
    retry_count     = state.get("qa_retry_count", 0)

    # Stage 1: Factual accuracy
    factual_prompt = f"""TASK: Stage 1 — Factual Accuracy Review

VALIDATED RESEARCH DATA (ground truth):
{raw_research[:1500]}

DRAFT TEXT TO REVIEW:
{draft_text[:1500]}

Check every factual claim against the research data. Flag hallucinations.
End with exactly: {PASS_SIGNAL} or {FAIL_SIGNAL}"""

    log.debug("Inspector: Stage 1 — factual review.")
    stage1_report = chat(SYSTEM_PROMPT, factual_prompt, temperature=0.1, max_tokens=512)
    stage1_passed = PASS_SIGNAL in stage1_report
    log.debug(f"Inspector: Stage 1 verdict → {'PASS' if stage1_passed else 'FAIL'}")
    post_message(job_id, "inspector", f"Stage 1 (Factual Accuracy): {'✅ PASS' if stage1_passed else '❌ FAIL'}", "success" if stage1_passed else "warning")

    # Stage 2: Brand compliance
    brand_prompt = f"""TASK: Stage 2 — Brand Compliance Review

BRAND GUIDELINES:
{brand_guidelines or "No brand guidelines provided."}

FORMATTING CODE:
{formatting_code[:1500]}

FILE OUTPUT EXISTS: {"Yes" if tdd_passed else "No — script failed"}
OUTPUT FORMAT: {output_format.upper()}

Verify brand colors, fonts, and layout. Flag deviations.
End with exactly: {PASS_SIGNAL} or {FAIL_SIGNAL}"""

    log.debug("Inspector: Stage 2 — brand compliance review.")
    stage2_report = chat(SYSTEM_PROMPT, brand_prompt, temperature=0.1, max_tokens=512)
    stage2_passed = PASS_SIGNAL in stage2_report
    log.debug(f"Inspector: Stage 2 verdict → {'PASS' if stage2_passed else 'FAIL'}")
    log.debug(f"Inspector: tdd_passed={tdd_passed} | overall qa_passed={stage1_passed and stage2_passed and tdd_passed}")
    post_message(job_id, "inspector", f"Stage 2 (Brand Compliance): {'✅ PASS' if stage2_passed else '❌ FAIL'}", "success" if stage2_passed else "warning")

    qa_passed = stage1_passed and stage2_passed and tdd_passed
    qa_report = f"## Stage 1: Factual Accuracy\n{stage1_report}\n\n## Stage 2: Brand Compliance\n{stage2_report}"

    error_log = state.get("error_log", "")
    if not qa_passed:
        post_message(job_id, "inspector", f"⚠️ QA FAILED (retry {retry_count}). Running systematic debug...", "warning")
        debug_prompt = build_debug_prompt(
            error_description=f"QA FAILED on retry {retry_count}",
            stage1_report=stage1_report,
            stage2_report=stage2_report,
            formatting_code=formatting_code,
        )
        error_log = chat(SYSTEM_PROMPT, debug_prompt, temperature=0.1, max_tokens=512)
        log.warning(f"Inspector: QA FAILED (retry {retry_count}). Root cause traced.")
    else:
        log.info(f"Inspector: QA PASSED on attempt {retry_count + 1}.")
        post_message(job_id, "inspector", f"✅ QA PASSED on attempt {retry_count + 1}. @orchestrator document is approved and ready for download!", "success")

    return {
        **state,
        "qa_passed": qa_passed,
        "qa_report": qa_report,
        "qa_retry_count": retry_count + (0 if qa_passed else 1),
        "error_log": error_log,
    }
