"""
app/tools/document_skills/pdf_builder.py

Builds a branded PDF from draft text using reportlab.

Layout:
  - Cover page: document title + brand bar
  - Body pages: section headings, paragraphs, bullet lists
  - Page header/footer on every body page
  - Brand colors: Navy #1A1A2E, Crimson #E94560, Off-white #EAEAEA
"""

import re
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    PageBreak, KeepTogether,
)
from reportlab.platypus.flowables import Flowable


# ── Brand tokens ──────────────────────────────────────────────────────────────
NAVY    = colors.HexColor("#1A1A2E")
CRIMSON = colors.HexColor("#E94560")
LIGHT   = colors.HexColor("#EAEAEA")
GREY    = colors.HexColor("#888888")
WHITE   = colors.white
BLACK   = colors.HexColor("#1a1a1a")


# ── Colored rule flowable ─────────────────────────────────────────────────────
class ColorBar(Flowable):
    """A full-width colored horizontal bar."""
    def __init__(self, height=4, color=CRIMSON):
        super().__init__()
        self.bar_height = height
        self.color = color
        self.width = 0

    def wrap(self, available_width, available_height):
        self.width = available_width
        return available_width, self.bar_height

    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.rect(0, 0, self.width, self.bar_height, fill=1, stroke=0)


# ── Page template callbacks ───────────────────────────────────────────────────
def _make_page_callbacks(title: str):
    """Return onFirstPage and onLaterPages callbacks for header/footer."""

    def _header_footer(canvas, doc):
        canvas.saveState()
        w, h = A4

        # Header bar
        canvas.setFillColor(NAVY)
        canvas.rect(0, h - 1.2 * cm, w, 1.2 * cm, fill=1, stroke=0)
        canvas.setFillColor(LIGHT)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawString(2 * cm, h - 0.85 * cm, "AgentPress")
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(w - 2 * cm, h - 0.85 * cm, title[:60])

        # Crimson accent line under header
        canvas.setFillColor(CRIMSON)
        canvas.rect(0, h - 1.25 * cm, w, 0.05 * cm, fill=1, stroke=0)

        # Footer
        canvas.setFillColor(GREY)
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(2 * cm, 0.7 * cm, "CONFIDENTIAL — AgentPress Internal")
        canvas.drawRightString(w - 2 * cm, 0.7 * cm, f"Page {doc.page}")

        canvas.restoreState()

    def _first_page(canvas, doc):
        # Cover page — no header/footer
        pass

    return _first_page, _header_footer


# ── Style sheet ───────────────────────────────────────────────────────────────
def _build_styles():
    base = getSampleStyleSheet()

    styles = {
        "cover_title": ParagraphStyle(
            "CoverTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=28,
            textColor=WHITE,
            leading=34,
            alignment=TA_LEFT,
            spaceAfter=12,
        ),
        "cover_sub": ParagraphStyle(
            "CoverSub",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=12,
            textColor=LIGHT,
            leading=18,
            alignment=TA_LEFT,
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=CRIMSON,
            leading=20,
            spaceBefore=18,
            spaceAfter=6,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=NAVY,
            leading=17,
            spaceBefore=12,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10.5,
            textColor=BLACK,
            leading=16,
            spaceBefore=2,
            spaceAfter=4,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10.5,
            textColor=BLACK,
            leading=15,
            leftIndent=16,
            firstLineIndent=0,
            spaceBefore=1,
            spaceAfter=2,
            bulletIndent=4,
            bulletFontName="Helvetica",
            bulletFontSize=10,
            bulletColor=CRIMSON,
        ),
        "footer_note": ParagraphStyle(
            "FooterNote",
            parent=base["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            textColor=GREY,
            alignment=TA_CENTER,
        ),
    }
    return styles


# ── Cover page builder ────────────────────────────────────────────────────────
def _build_cover(title: str, styles: dict) -> list:
    """Build a branded cover page."""
    story = []

    # Navy background block (simulated with a large colored spacer + text)
    # We use a canvas-level approach via a custom flowable
    class CoverBackground(Flowable):
        def __init__(self, doc_title):
            super().__init__()
            self.doc_title = doc_title

        def wrap(self, aw, ah):
            return aw, ah

        def draw(self):
            w, h = A4
            c = self.canv

            # Full navy background
            c.setFillColor(NAVY)
            c.rect(0, 0, w, h, fill=1, stroke=0)

            # Crimson accent bar at bottom
            c.setFillColor(CRIMSON)
            c.rect(0, 0, w, 1.2 * cm, fill=1, stroke=0)

            # Crimson side accent
            c.setFillColor(CRIMSON)
            c.rect(0, h * 0.35, 0.5 * cm, h * 0.65, fill=1, stroke=0)

            # AgentPress wordmark
            c.setFillColor(LIGHT)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(1.5 * cm, h - 2 * cm, "AgentPress")

            # Document title
            c.setFillColor(WHITE)
            c.setFont("Helvetica-Bold", 26)
            # Word-wrap manually for long titles
            words = self.doc_title.split()
            lines, line = [], []
            for word in words:
                line.append(word)
                if len(" ".join(line)) > 30:
                    lines.append(" ".join(line[:-1]))
                    line = [word]
            if line:
                lines.append(" ".join(line))

            y = h * 0.55
            for ln in lines[:4]:
                c.drawString(1.5 * cm, y, ln)
                y -= 3.2 * cm

            # Subtitle
            c.setFillColor(LIGHT)
            c.setFont("Helvetica", 11)
            c.drawString(1.5 * cm, h * 0.32, "Generated by AgentPress Autonomous Pipeline")

            # Bottom label
            c.setFillColor(WHITE)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(1.5 * cm, 0.35 * cm, "CONFIDENTIAL")

    story.append(CoverBackground(title))
    story.append(PageBreak())
    return story


# ── Section parser ────────────────────────────────────────────────────────────
def _parse_sections(draft_text: str) -> list[dict]:
    """Split draft into sections by ## headings."""
    raw = re.split(r"^##\s+", draft_text, flags=re.MULTILINE)
    sections = []
    for block in raw:
        block = block.strip()
        if not block:
            continue
        lines = block.splitlines()
        title = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", lines[0]).strip()
        body = lines[1:]
        sections.append({"title": title, "body": body})
    return sections


def _clean(text: str) -> str:
    text = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", text)
    text = re.sub(r"`(.*?)`", r"\1", text)
    return text.strip()


# ── Main builder ──────────────────────────────────────────────────────────────
def build_pdf(draft_text: str, output_path: str) -> bool:
    """
    Build a branded PDF from draft text.

    Args:
        draft_text: Synthesizer output with ## section headings.
        output_path: Absolute path to write the .pdf file.

    Returns:
        True if the file was created successfully.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    styles = _build_styles()
    sections = _parse_sections(draft_text)

    # Derive document title from first section heading
    doc_title = sections[0]["title"] if sections else "AgentPress Document"

    first_page_cb, later_pages_cb = _make_page_callbacks(doc_title)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2 * cm,
        title=doc_title,
        author="AgentPress",
    )

    story = []

    # Cover page
    story += _build_cover(doc_title, styles)

    # Body sections
    for si, section in enumerate(sections):
        block = []

        # Section heading
        block.append(Paragraph(section["title"], styles["h1"]))
        block.append(HRFlowable(
            width="100%", thickness=1.5, color=CRIMSON,
            spaceAfter=6, spaceBefore=0,
        ))

        for line in section["body"]:
            raw = line.strip()
            if not raw:
                block.append(Spacer(1, 0.2 * cm))
                continue

            cleaned = _clean(raw)

            # Sub-heading: lines starting with ### or all-caps short lines
            if raw.startswith("### "):
                block.append(Paragraph(cleaned.lstrip("# "), styles["h2"]))

            # Bullet point
            elif re.match(r"^[-•*]\s+", raw) or re.match(r"^\d+\.\s+", raw):
                text = re.sub(r"^[-•*\d.]+\s+", "", cleaned)
                block.append(Paragraph(f"• {text}", styles["bullet"]))

            # Regular paragraph
            else:
                block.append(Paragraph(cleaned, styles["body"]))

        # Keep heading + first few lines together to avoid orphans
        story.append(KeepTogether(block[:4]))
        story += block[4:]
        story.append(Spacer(1, 0.4 * cm))

    # Build with header/footer on body pages
    doc.build(
        story,
        onFirstPage=first_page_cb,
        onLaterPages=later_pages_cb,
    )

    assert Path(output_path).exists()
    return True
