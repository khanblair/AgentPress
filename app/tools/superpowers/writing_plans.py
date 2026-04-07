"""
app/tools/superpowers/writing_plans.py
"""

def build_task_plan(document_spec: str, output_format: str) -> str:
    return f"""Based on the following Document Spec, create a step-by-step task plan for an autonomous agent team.

DOCUMENT SPEC:
{document_spec}

OUTPUT FORMAT: {output_format}

Each task must be isolated and actionable. 
Format: A numbered list of tasks.
Example:
1. Research market trends for [X].
2. Draft the executive summary focusing on [Y].
3. Analyze competitor data for [Z].
...

Output only the numbered list."""
