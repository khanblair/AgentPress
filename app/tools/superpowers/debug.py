"""
app/tools/superpowers/debug.py
"""

def build_debug_prompt(error_description: str, stage1_report: str, stage2_report: str, formatting_code: str) -> str:
    return f"""You are a systematic debugging expert. 
A document pipeline run failed QA inspection. You must trace the root cause.

ERROR DESCRIPTION:
{error_description}

QA STAGE 1 (Factual):
{stage1_report}

QA STAGE 2 (Brand):
{stage2_report}

DESIGNER CODE:
```python
{formatting_code}
```

INSTRUCTIONS:
1. Identify the specific line or logic in the code that caused the failure.
2. Determine if the failure was due to missing data, incorrect formatting API usage, or brand goal violation.
3. Suggest a specific code fix or a new tool script that could prevent this failure.

Output a structured Debug Report explaining the ROOT CAUSE."""
