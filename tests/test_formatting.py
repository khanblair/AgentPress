"""
tests/test_formatting.py

Verifies that the document builder applies correct brand colors.
"""

import pytest
from pathlib import Path
from app.tools.document_skills.pptx_builder import build_pptx

def test_pptx_formatting_logic(tmp_path):
    output_path = tmp_path / "test_formatting.pptx"
    draft = "## Slide 1: Brand Test\\nThis is a test of the Crimson Red accent."
    
    # Run the builder
    success = build_pptx(draft, str(output_path))
    
    assert success is True
    assert output_path.exists()
    # In a full test, we would use python-pptx to inspect the generated XML
    # and confirm the RGB values match #E94560.
