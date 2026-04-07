"""
app/evolution_engine/delta_parser.py

Diffs AI-generated output vs. human-corrected version.
Returns a structured correction_delta dict describing the change.
"""

import difflib
import json
import re


def parse_delta(original: str, corrected: str) -> str:
    """
    Compare original AI output to human-corrected version.
    Returns a JSON-serialised delta summary for rule_resolver and meta_engineer.
    """
    original_lines = original.splitlines(keepends=True)
    corrected_lines = corrected.splitlines(keepends=True)

    diff = list(difflib.unified_diff(
        original_lines,
        corrected_lines,
        fromfile="ai_output",
        tofile="human_corrected",
        lineterm="",
    ))

    added = [l[1:].strip() for l in diff if l.startswith("+") and not l.startswith("+++")]
    removed = [l[1:].strip() for l in diff if l.startswith("-") and not l.startswith("---")]

    # Classify the type of correction
    correction_type = _classify_correction(added, removed)

    delta = {
        "correction_type": correction_type,
        "lines_added": added[:20],         # cap for readability
        "lines_removed": removed[:20],
        "diff_size": len(diff),
        "summary": f"{len(added)} line(s) added, {len(removed)} line(s) removed. Type: {correction_type}",
    }

    return json.dumps(delta, indent=2)


def _classify_correction(added: list[str], removed: list[str]) -> str:
    """Heuristically classify what kind of correction was made."""
    all_changes = " ".join(added + removed).lower()

    if any(kw in all_changes for kw in ["#", "rgb", "hex", "color", "colour", "font", "style"]):
        return "brand_visual"
    if any(kw in all_changes for kw in ["tone", "voice", "formal", "casual", "professional"]):
        return "brand_tone"
    if any(kw in all_changes for kw in ["fact", "data", "statistic", "percent", "number", "%"]):
        return "factual"
    if any(kw in all_changes for kw in ["structure", "section", "heading", "order", "layout"]):
        return "structure"
    return "general"
