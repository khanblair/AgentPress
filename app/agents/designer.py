"""
app/agents/designer.py — Agent 4: Brand & Format Specialist
Model: qwen/qwen3-coder:free (via OpenRouter)

Responsibilities:
 - Read brand.md for hex codes, fonts, logo paths, layout rules
 - Write executable Python (python-docx / python-pptx) to format draft_text
 - Apply TDD cycle: write test → run → fix → refactor
 - Save compiled file to OUTPUT_DIR, store path in formatted_file_path
"""

import os
import subprocess
import tempfile
from pathlib import Path
from openai import OpenAI

from app.agents.state import AgentState
from app.core.config import settings
from app.core.logger import setup_logger

log = setup_logger("designer")

client = OpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url=settings.OPENROUTER_BASE_URL,
)

OUTPUT_DIR = Path(settings.OUTPUT_DIR)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _load_brand() -> str:
    try:
        with open("app/knowledge_base/brand.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "# No brand guidelines found. Use professional defaults."


def _execute_script(script: str, output_path: str) -> tuple[bool, str]:
    """Write script to temp file and execute it. Returns (success, stderr)."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as f:
        f.write(script)
        tmp_path = f.name
    try:
        result = subprocess.run(
            ["python", tmp_path],
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, "OUTPUT_PATH": output_path},
        )
        success = result.returncode == 0
        stderr = result.stderr.strip()
        if success:
            log.info(f"Designer: Script executed successfully → {output_path}")
        else:
            log.error(f"Designer: Script failed:\n{stderr}")
        return success, stderr
    except subprocess.TimeoutExpired:
        return False, "Script execution timed out (60s)"
    finally:
        os.unlink(tmp_path)


def run_designer(state: AgentState) -> AgentState:
    log.info("Designer: Starting brand formatting phase (TDD).")

    draft_text = state.get("draft_text", "")
    output_format = state.get("output_format", "docx")
    session_id = state.get("session_id", "output")
    brand_guidelines = _load_brand()
    error_context = state.get("error_log", "")
    retry_count = state.get("qa_retry_count", 0)

    output_path = str(OUTPUT_DIR / f"{session_id}.{output_format}")

    # Build the code-generation prompt
    coding_prompt = f"""You are an expert Python developer writing a document formatting script.

BRAND GUIDELINES:
{brand_guidelines}

DOCUMENT CONTENT (draft text with section headings):
{draft_text[:3000]}  

OUTPUT FORMAT: {output_format.upper()}
OUTPUT FILE PATH: {output_path}

{"PREVIOUS ERRORS TO FIX:\\n" + error_context if error_context else ""}
{"RETRY ATTEMPT: " + str(retry_count) if retry_count > 0 else ""}

INSTRUCTIONS:
1. Write a complete, runnable Python script using {"python-pptx" if output_format == "pptx" else "python-docx" if output_format == "docx" else "openpyxl"}.
2. Apply brand colors, fonts, and layout from the guidelines above.
3. Parse the draft text by section headings (## lines) to split content.
4. Save the file to exactly this path: {output_path}
5. The script must be self-contained — no user input, no missing imports.
6. Follow TDD: at the end of the script, add an assert that the output file exists.

OUTPUT: Only the Python code, no explanations, no markdown fences."""

    log.debug(f"Designer: Calling {settings.DESIGNER_MODEL} (attempt {retry_count + 1}).")
    response = client.chat.completions.create(
        model=settings.DESIGNER_MODEL,
        messages=[{"role": "user", "content": coding_prompt}],
        temperature=0.1,
    )
    formatting_code = response.choices[0].message.content.strip()
    # Strip any accidental markdown fences
    if formatting_code.startswith("```"):
        lines = formatting_code.splitlines()
        formatting_code = "\n".join(
            line for line in lines if not line.startswith("```")
        )

    # Execute the script (TDD RED → GREEN)
    tdd_passed, exec_error = _execute_script(formatting_code, output_path)

    new_error_log = exec_error if not tdd_passed else state.get("error_log", "")

    return {
        **state,
        "formatted_file_path": output_path if tdd_passed else "",
        "formatting_code": formatting_code,
        "tdd_passed": tdd_passed,
        "error_log": new_error_log,
    }
