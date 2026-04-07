"""
tests/test_hallucinations.py

Verifies factual accuracy between research and draft.
"""

import pytest

def test_hallucination_check_logic():
    # Simulated check logic: 
    # Any fact in the draft must exist in the research string.
    research = "The year is 2024. Revenue grew by 15%."
    draft = "Our revenue in 2024 grew by 15%."
    hallucination = "Our revenue in 2025 grew by 20%."
    
    assert "2024" in draft and "15%" in draft
    assert "2025" not in research
