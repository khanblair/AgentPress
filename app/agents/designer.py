"""
app/agents/designer.py — Agent 4: Brand & Format Specialist
Skill: Python code generation for document formatting (TDD)
"""

import os
import subprocess
import tempfile
from pathlib import Path
from app.agents.state import AgentState
from app.agents.client import chat
from app.core.config import settings
from app.core.logger import setup_logger

log = setup_logger("designer")

OUTPUT_DIR = Path(settings.OUTPUT_DIR)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = """You are the Brand & Format Specialist for AgentPress, an autonomous document pipeline.
Your role is writing executable Python scripts that compile formatted documents.
You use python-docx, python-pptx, or openpyxl depending on the output format.
You apply brand colors, fonts, and layout rules precisely.
You output ONLY raw Python code — no markdown fences, no explanations."""


def _load_brand() -> str:
    try:
        with open("app/knowledge_base/brand.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Use professional defaults."


def _execute_script(script: str, output_path: str) -> tuple[bool, str]:
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as f:
        f.write(script)
        tmp_path = f.name
    try:
        result = subprocess.run(
            ["python", tmp_path],
            capture_output=True, text=True, timeout=60,
            env={**os.environ, "OUTPUT_PATH": output_path},
        )
        success = result.returncode == 0
        if success:
            log.info(f"Designer: Script executed → {output_path}")
        else:
            log.error(f"Designer: Script failed:\n{result.stderr.strip()}")
        return success, result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "Script execution timed out (60s)"
    finally:
        os.unlink(tmp_path)


def run_designer(state: AgentState) -> AgentState:
    log.info("Designer: Starting brand formatting phase (TDD).")

    draft_text      = state.get("draft_text", "")
    output_format   = state.get("output_format", "docx")
    session_id      = state.get("session_id", "output")
    brand_guidelines = _load_brand()
    error_context   = state.get("error_log", "")
    retry_count     = state.get("qa_retry_count", 0)
    output_path     = str(OUTPUT_DIR / f"{session_id}.{output_format}")
    builder_pkg     = "python-pptx" if output_format == "pptx" else "python-docx" if output_format == "docx" else "openpyxl"

    error_header = f"PREVIOUS ERRORS TO FIX:\n{error_context}\n" if error_context else ""
    retry_header = f"RETRY ATTEMPT: {retry_count}\n" if retry_count > 0 else ""

    coding_prompt = f"""Write a complete, runnable Python script using {builder_pkg}.

BRAND GUIDELINES:
{brand_guidelines}

DOCUMENT CONTENT:
{draft_text[:2000]}

OUTPUT FORMAT: {output_format.upper()}
OUTPUT FILE PATH: {output_path}

{error_header}{retry_header}

REQUIREMENTS:
1. Apply brand colors and fonts from the guidelines.
2. Parse draft text by ## headings to split sections.
3. Save the file to exactly: {output_path}
4. Self-contained — no missing imports, no user input.
5. End with: assert Path("{output_path}").exists()"""

    log.debug(f"Designer: Calling {settings.MODEL} (attempt {retry_count + 1}).")
    formatting_code = chat(SYSTEM_PROMPT, coding_prompt, temperature=0.1, max_tokens=1024)

    # Strip accidental markdown fences
    if formatting_code.startswith("```"):
        formatting_code = "\n".join(
            line for line in formatting_code.splitlines()
            if not line.startswith("```")
        )

    tdd_passed, exec_error = _execute_script(formatting_code, output_path)

    return {
        **state,
        "formatted_file_path": output_path if tdd_passed else "",
        "formatting_code": formatting_code,
        "tdd_passed": tdd_passed,
        "error_log": exec_error if not tdd_passed else state.get("error_log", ""),
    }
