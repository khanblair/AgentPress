"""
app/evolution_engine/rule_resolver.py

Updates brand.md and user.md when human corrections imply persistent rule changes.
Resolves contradictions: newer + user-confirmed rules win.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path


BRAND_MD = Path("app/knowledge_base/brand.md")
USER_MD = Path("app/knowledge_base/user.md")


def resolve_rules(delta_json: str) -> None:
    """
    Parse the correction delta and apply persistent rule updates to
    brand.md (visual/tone) or user.md (preferences/structure).

    Args:
        delta_json: JSON string from delta_parser.parse_delta()
    """
    try:
        delta = json.loads(delta_json)
    except json.JSONDecodeError:
        return  # Malformed delta — skip silently

    correction_type = delta.get("correction_type", "general")
    lines_added = delta.get("lines_added", [])

    if not lines_added:
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    entry = "\n".join(f"- {line}" for line in lines_added[:10] if line.strip())

    if correction_type in ("brand_visual", "brand_tone"):
        _append_rule(
            path=BRAND_MD,
            section="## Auto-Updated Rules",
            entry=f"\n**[{timestamp}] Correction ({correction_type}):**\n{entry}",
        )
    elif correction_type in ("factual", "structure", "general"):
        _append_rule(
            path=USER_MD,
            section="## User Preferences",
            entry=f"\n**[{timestamp}] Correction ({correction_type}):**\n{entry}",
        )


def _append_rule(path: Path, section: str, entry: str) -> None:
    """Append a new rule entry to the appropriate section in an .md file."""
    if not path.exists():
        path.write_text(f"# Knowledge Base\n\n{section}\n{entry}\n", encoding="utf-8")
        return

    content = path.read_text(encoding="utf-8")
    if section in content:
        content = content.replace(section, section + entry)
    else:
        content += f"\n\n{section}\n{entry}\n"

    # Contradiction resolution: if an older rule conflicts with a newer one,
    # mark the older one as superseded rather than deleting it.
    content = _mark_superseded(content, entry)
    path.write_text(content, encoding="utf-8")


def _mark_superseded(content: str, new_entry: str) -> str:
    """
    Simple heuristic: if two rules contain the same key terms,
    mark the older one as [SUPERSEDED].
    """
    key_terms = re.findall(r"\b(color|hex|font|tone|format|style)\b", new_entry, re.IGNORECASE)
    if not key_terms:
        return content

    lines = content.splitlines()
    result = []
    for line in lines:
        if any(term.lower() in line.lower() for term in key_terms):
            if "[SUPERSEDED]" not in line and "[" not in line[:5]:
                line = f"~~{line}~~ [SUPERSEDED]"
        result.append(line)
    return "\n".join(result)
