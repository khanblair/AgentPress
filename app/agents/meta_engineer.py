"""
app/agents/meta_engineer.py — Agent 6: The Meta-Engineer (Evolution Engine)
Skill: Writing new reusable tool scripts to fix recurring failures
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from app.agents.state import AgentState
from app.agents.client import chat
from app.core.config import settings
from app.core.logger import setup_logger
from app.evolution_engine.skill_creator import create_skill
from app.evolution_engine.delta_parser import parse_delta
from app.evolution_engine.rule_resolver import resolve_rules

log = setup_logger("meta_engineer")

EVOLUTIONS_DIR = Path("docs/evolutions")
EVOLUTIONS_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = """You are the Meta-Engineer for AgentPress, an autonomous document pipeline.
Your role is self-improvement — writing new Python tool scripts to fix recurring pipeline failures.
You write clean, importable Python functions with clear docstrings.
You output ONLY raw Python code — no markdown fences, no explanations."""


def run_meta_engineer(state: AgentState) -> AgentState:
    log.info("Meta-Engineer: Evolution loop triggered.")

    error_log           = state.get("error_log", "No error log provided.")
    formatting_code     = state.get("formatting_code", "")
    output_format       = state.get("output_format", "docx")
    correction_original = state.get("correction_original", "")
    correction_edited   = state.get("correction_edited", "")
    session_id          = state.get("session_id", str(uuid.uuid4()))

    # Parse human correction delta if provided
    delta = ""
    if correction_original and correction_edited:
        delta = parse_delta(correction_original, correction_edited)
        resolve_rules(delta)
        log.info("Meta-Engineer: Correction delta parsed and rules updated.")

    skill_prompt = f"""Write a reusable Python function to fix this recurring pipeline failure.

FAILURE DESCRIPTION:
{error_log}

FAILED CODE:
{formatting_code[:1500]}

OUTPUT FORMAT: {output_format.upper()}
CORRECTION DELTA: {delta or "No human correction provided."}

Write a function: apply_brand_fix(draft_text: str, output_path: str) -> bool
- Fix the root cause above
- Importable as a reusable skill (no __main__ block)
- Include a docstring explaining the fix"""

    log.debug(f"Meta-Engineer: Calling {settings.MODEL}.")
    skill_code = chat(SYSTEM_PROMPT, skill_prompt, temperature=0.1, max_tokens=1024)
    if skill_code.startswith("```"):
        skill_code = "\n".join(l for l in skill_code.splitlines() if not l.startswith("```"))

    skill_filename = f"brand_fix_{session_id[:8]}.py"
    new_skill_path = create_skill(filename=skill_filename, code=skill_code, category="document_skills")
    log.info(f"Meta-Engineer: New skill written → {new_skill_path}")

    # Write regression test
    test_code = f'''"""Auto-generated regression test — Session {session_id[:8]}"""
import pytest
from pathlib import Path
from app.tools.document_skills.{skill_filename[:-3]} import apply_brand_fix

def test_brand_fix_creates_output(tmp_path):
    output_path = str(tmp_path / "test_output.{output_format}")
    draft = "## Section 1\\nTest content."
    result = apply_brand_fix(draft, output_path)
    assert result is True
    assert Path(output_path).exists()
'''
    test_path = Path(f"tests/test_evolution_{session_id[:8]}.py")
    test_path.write_text(test_code, encoding="utf-8")
    log.info(f"Meta-Engineer: Regression test written → {test_path}")

    # Publish changelog
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    changelog = f"""# Evolution: {skill_filename}
**Date:** {timestamp}
**Session:** `{session_id}`
**Trigger:** QA failed after {settings.MAX_QA_RETRIES} retries

## Root Cause
{error_log[:500]}

## Fix Applied
New skill `{skill_filename}` written to `app/tools/document_skills/`.

## Regression Test
`{test_path}` auto-generated.
"""
    changelog_path = EVOLUTIONS_DIR / f"{session_id[:8]}.md"
    changelog_path.write_text(changelog, encoding="utf-8")
    log.info(f"Meta-Engineer: Changelog published → {changelog_path}")

    return {
        **state,
        "evolution_triggered": True,
        "new_skill_path": str(new_skill_path),
        "evolution_changelog": changelog,
    }
