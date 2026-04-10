"""Auto-generated regression test — Session 2bd260fa"""
import pytest
from pathlib import Path
from app.tools.document_skills.brand_fix_2bd260fa import apply_brand_fix

def test_brand_fix_creates_output(tmp_path):
    output_path = str(tmp_path / "test_output.pptx")
    draft = "## Section 1\nTest content."
    result = apply_brand_fix(draft, output_path)
    assert result is True
    assert Path(output_path).exists()
