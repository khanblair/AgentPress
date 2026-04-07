"""
app/agents/meta_engineer.py — Agent 6: The Meta-Engineer (Evolution Engine)
Model: qwen/qwen3-coder:free (via OpenRouter)

Responsibilities:
 - Triggered when Inspector fails MAX_QA_RETRIES times
 - Reads error_log to understand the systemic failure
 - Writes a new reusable tool script in app/tools/
 - Generates a regression test for the new skill
 - Publishes a changelog entry to docs/evolutions/
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from openai import OpenAI

from app.agents.state import AgentState
from app.core.config import settings
from app.core.logger import setup_logger
from app.evolution_engine.skill_creator import create_skill
from app.evolution_engine.delta_parser import parse_delta
from app.evolution_engine.rule_resolver import resolve_rules

log = setup_logger("meta_engineer")

client = OpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url=settings.OPENROUTER_BASE_URL,
)

EVOLUTIONS_DIR = Path("docs/evolutions")
EVOLUTIONS_DIR.mkdir(parents=True, exist_ok=True)


def run_meta_engineer(state: AgentState) -> AgentState:
    log.info("Meta-Engineer: Evolution loop triggered.")

    error_log = state.get("error_log", "No error log provided.")
    formatting_code = state.get("formatting_code", "")
    output_format = state.get("output_format", "docx")
    correction_original = state.get("correction_original", "")
    correction_edited = state.get("correction_edited", "")
    session_id = state.get("session_id", str(uuid.uuid4()))

    # 1. Parse correction delta (if human correction was submitted)
    delta = ""
    if correction_original and correction_edited:
        delta = parse_delta(correction_original, correction_edited)
        resolve_rules(delta)  # Update brand.md / user.md if needed
        log.info("Meta-Engineer: Correction delta parsed and rules updated.")

    # 2. Ask the Meta-Engineer model to write a new repair skill
    skill_prompt = f"""You are a Python expert writing a reusable skill script to fix a recurring pipeline failure.

FAILURE DESCRIPTION:
{error_log}

FAILED FORMATTING CODE:
```python
{formatting_code[:2000]}
```

OUTPUT FORMAT: {output_format.upper()}
CORRECTION DELTA: {delta or "No human correction provided."}

TASK:
1. Write a new Python function called `apply_brand_fix(draft_text: str, output_path: str) -> bool`
2. This function must fix the root cause of the failure above.
3. It must be importable as a reusable skill (no __main__ block).
4. Include a docstring explaining exactly what the fix does.

OUTPUT: Only the Python code. No markdown fences."""

    log.debug(f"Meta-Engineer: Calling {settings.META_ENGINEER_MODEL}.")
    response = client.chat.completions.create(
        model=settings.META_ENGINEER_MODEL,
        messages=[{"role": "user", "content": skill_prompt}],
        temperature=0.1,
    )
    skill_code = response.choices[0].message.content.strip()
    if skill_code.startswith("```"):
        lines = skill_code.splitlines()
        skill_code = "\n".join(line for line in lines if not line.startswith("```"))

    # 3. Write the new skill to app/tools/document_skills/
    skill_filename = f"brand_fix_{session_id[:8]}.py"
    new_skill_path = create_skill(
        filename=skill_filename,
        code=skill_code,
        category="document_skills",
    )
    log.info(f"Meta-Engineer: New skill written → {new_skill_path}")

    # 4. Write regression test
    test_code = f"""\"\"\"Auto-generated regression test by Meta-Engineer — Session {session_id[:8]}\"\"\"
import pytest
from pathlib import Path
from app.tools.document_skills.{skill_filename[:-3]} import apply_brand_fix


def test_brand_fix_creates_output(tmp_path):
    output_path = str(tmp_path / "test_output.{output_format}")
    # Minimal draft text for regression
    draft = "## Section 1\\nTest content for brand fix regression."
    result = apply_brand_fix(draft, output_path)
    assert result is True, "apply_brand_fix must return True on success"
    assert Path(output_path).exists(), "Output file must be created"
"""
    test_path = Path(f"tests/test_evolution_{session_id[:8]}.py")
    test_path.write_text(test_code, encoding="utf-8")
    log.info(f"Meta-Engineer: Regression test written → {test_path}")

    # 5. Publish changelog to docs/evolutions/
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
`{test_path}` auto-generated to prevent regression.
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
