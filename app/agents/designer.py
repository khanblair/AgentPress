"""
app/agents/designer.py — Agent 4: Brand & Format Specialist
Skill: Calls deterministic document builders directly — no LLM code generation.

Pipeline:
  PPTX → app/tools/document_skills/pptx_builder.py
  DOCX → app/tools/document_skills/docx_builder.py
  XLSX → app/tools/document_skills/xlsx_builder.py (openpyxl)
  PDF  → reportlab fallback
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
    draft_text    = state.get("draft_text", "")
    output_format = state.get("output_format", "docx")
    session_id    = state.get("session_id", "output")
    output_path   = str(OUTPUT_DIR / f"{session_id}.{output_format}")

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
            tdd_passed = _build_xlsx(draft_text, output_path)

        elif output_format == "pdf":
            tdd_passed = _build_pdf(draft_text, output_path)

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


def _build_xlsx(draft_text: str, output_path: str) -> bool:
    """Build a basic Excel file from draft text sections."""
    import re
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active

    # Brand colors
    HEADER_FILL = PatternFill("solid", fgColor="1A1A2E")
    HEADER_FONT = Font(name="Calibri", bold=True, color="EAEAEA", size=12)
    ACCENT_FILL = PatternFill("solid", fgColor="E94560")
    BODY_FONT   = Font(name="Calibri", size=11)

    # Parse ## sections
    sections = re.split(r"^##\s+", draft_text, flags=re.MULTILINE)
    row = 1

    for section in sections:
        if not section.strip():
            continue
        lines = section.strip().splitlines()
        heading = lines[0].strip()

        # Section heading row
        cell = ws.cell(row=row, column=1, value=heading)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="left", vertical="center")
        ws.row_dimensions[row].height = 22
        row += 1

        # Body rows
        for line in lines[1:]:
            line = line.strip().lstrip("•-* ")
            if not line:
                continue
            # Try to split on tab or multiple spaces for table-like data
            parts = re.split(r"\t|  {2,}", line)
            for col, part in enumerate(parts, start=1):
                c = ws.cell(row=row, column=col, value=part.strip())
                c.font = BODY_FONT
            row += 1

        row += 1  # blank row between sections

    # Auto-size columns
    for col in ws.columns:
        max_len = max((len(str(c.value or "")) for c in col), default=10)
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(max_len + 4, 60)

    # Footer
    ws.cell(row=row + 1, column=1, value="CONFIDENTIAL - AgentPress Internal").font = Font(
        name="Calibri", size=9, italic=True, color="888888"
    )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    assert Path(output_path).exists()
    return True


def _build_pdf(draft_text: str, output_path: str) -> bool:
    """Build a basic PDF from draft text using reportlab."""
    import re
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    BRAND_NAVY  = colors.HexColor("#1A1A2E")
    BRAND_RED   = colors.HexColor("#E94560")

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            leftMargin=3*cm, rightMargin=3*cm,
                            topMargin=2.5*cm, bottomMargin=2.5*cm)
    styles = getSampleStyleSheet()
    heading_style = ParagraphStyle("BrandH1", parent=styles["Heading1"],
                                   textColor=BRAND_RED, fontName="Helvetica-Bold", fontSize=14)
    body_style    = ParagraphStyle("BrandBody", parent=styles["Normal"],
                                   textColor=BRAND_NAVY, fontName="Helvetica", fontSize=11,
                                   leading=16)

    story = []
    sections = re.split(r"^##\s+", draft_text, flags=re.MULTILINE)

    for section in sections:
        if not section.strip():
            continue
        lines = section.strip().splitlines()
        story.append(Paragraph(lines[0].strip(), heading_style))
        story.append(Spacer(1, 0.3*cm))
        for line in lines[1:]:
            line = line.strip()
            if line:
                story.append(Paragraph(line.lstrip("•-* "), body_style))
        story.append(Spacer(1, 0.5*cm))

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc.build(story)
    assert Path(output_path).exists()
    return True
