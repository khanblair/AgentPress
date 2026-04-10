"""
app/agents/designer.py — Agent 4: Brand & Format Specialist
Skill: Calls deterministic document builders directly — no LLM code generation.

Pipeline:
  PPTX → app/tools/document_skills/pptx_builder.py
  DOCX → app/tools/document_skills/docx_builder.py
  XLSX → app/tools/document_skills/xlsx_builder.py
  PDF  → app/tools/document_skills/pdf_builder.py
"""

from pathlib import Path
from app.agents.state import AgentState
from app.agents.messenger import post_message
from app.core.config import settings
from app.core.logger import setup_logger

log = setup_logger("designer")

OUTPUT_DIR = Path(settings.OUTPUT_DIR)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run_designer(state: AgentState) -> AgentState:
    draft_text      = state.get("draft_text", "")
    output_format   = state.get("output_format", "docx")
    session_id      = state.get("session_id", "output")
    document_title  = state.get("document_title", "").strip()

    # Build a readable filename: "q3-market-analysis_a1b2c3d4.docx"
    short_id = session_id[:8] if session_id else "output"
    if document_title:
        filename = f"{document_title}_{short_id}.{output_format}"
    else:
        filename = f"{short_id}.{output_format}"

    output_path = str(OUTPUT_DIR / filename)

    log.info("Designer: Starting brand formatting phase.")
    log.debug(f"Designer: format={output_format} | output={output_path} | draft_chars={len(draft_text)}")
    job_id = state.get("job_id", "")
    post_message(job_id, "designer", f"🎨 On it @synthesizer. Building {output_format.upper()} with brand colors (#1A1A2E, #E94560)...")

    tdd_passed = False
    exec_error = ""

    try:
        if output_format == "pptx":
            from app.tools.document_skills.pptx_builder import build_pptx
            tdd_passed = build_pptx(draft_text, output_path)

        elif output_format == "docx":
            from app.tools.document_skills.docx_builder import build_docx
            tdd_passed = build_docx(draft_text, output_path)

        elif output_format == "xlsx":
            from app.tools.document_skills.xlsx_builder import build_xlsx
            tdd_passed = build_xlsx(draft_text, output_path)

        elif output_format == "pdf":
            from app.tools.document_skills.pdf_builder import build_pdf
            tdd_passed = build_pdf(draft_text, output_path)

        else:
            raise ValueError(f"Unsupported output format: {output_format}")

        if tdd_passed:
            log.info(f"Designer: Document built → {output_path}")
            log.debug(f"Designer: File size = {Path(output_path).stat().st_size} bytes")
            post_message(job_id, "designer", f"✅ Document built → `{Path(output_path).name}` ({Path(output_path).stat().st_size // 1024} KB). @inspector please review.", "success")
        else:
            exec_error = f"Builder returned False for {output_format}"
            log.error(f"Designer: {exec_error}")

    except Exception as e:
        exec_error = str(e)
        log.error(f"Designer: Build failed — {exec_error}")
        post_message(job_id, "designer", f"❌ Build failed: {exec_error[:200]}", "error")
        tdd_passed = False

    return {
        **state,
        "formatted_file_path": output_path if tdd_passed else "",
        "formatting_code": f"# Used {output_format}_builder skill directly",
        "tdd_passed": tdd_passed,
        "error_log": exec_error if not tdd_passed else state.get("error_log", ""),
    }
