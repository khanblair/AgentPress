# Evolution Log

Every time the **Meta-Engineer** agent is triggered — either by QA failing after max retries or by a human correction — it writes a new Python skill to fix the root cause. Each entry below is an auto-generated changelog from one of those events.

## What Gets Logged

Each evolution entry records:

- **Date & session ID** of the triggering run
- **Root cause** — the error or QA failure that triggered the evolution
- **Fix applied** — the new skill written to `app/tools/document_skills/`
- **Regression test** — the auto-generated pytest file path

## How It Works

```python
# Meta-Engineer writes a reusable fix function
def apply_brand_fix(draft_text: str, output_path: str) -> bool:
    # Fix the root cause
    # Return True on success
    ...
```

The skill is registered in `app/tools/skills_registry.json` and available for all future pipeline runs.

---

*New entries are appended automatically each time the Meta-Engineer is triggered.*
