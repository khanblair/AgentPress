# Architecture

AgentPress is built on a **FastAPI + LangGraph** backend with a **React + Vite** frontend.

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    React + Vite UI                       │
│  Workspace · Pipeline · Review · Chat · Skills · Analytics│
└────────────────────┬────────────────────────────────────┘
                     │ HTTP / SSE
┌────────────────────▼────────────────────────────────────┐
│                  FastAPI Backend                          │
│  POST /generate · GET /status · GET /jobs/:id/stream     │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              LangGraph StateGraph                         │
│  orchestrator → researcher → synthesizer                  │
│  → designer → inspector → (meta_engineer)                 │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ChromaDB       SQLite      OpenRouter
  (memory)      (sessions)     (LLM)
```

## Pipeline State

All data flows through a single `AgentState` TypedDict — a Redux-style shared state object that every agent reads from and writes to.

```python
class AgentState(TypedDict, total=False):
    user_prompt: str          # Raw user request
    document_spec: str        # Orchestrator's document specification
    document_title: str       # Human-readable filename slug
    task_plan: List[str]      # Ordered sub-tasks
    output_format: str        # pptx | docx | xlsx | pdf
    raw_research: str         # Researcher's validated data
    draft_text: str           # Synthesizer's content draft
    formatted_file_path: str  # Final output file path
    qa_passed: bool           # Inspector's verdict
    evolution_triggered: bool # Meta-Engineer activation flag
```

## Real-Time Streaming

The pipeline runs in a **thread pool executor** to keep the async event loop free. Agent messages are streamed to the UI via **Server-Sent Events** at `GET /jobs/{job_id}/stream`, polling the in-memory messenger every 200ms.

## Evolution Engine

When QA fails after `MAX_QA_RETRIES` (default: 3), the Meta-Engineer:

1. **Delta Parser** — diffs AI output vs. human corrections
2. **Rule Resolver** — updates `brand.md` / `user.md` with persistent rules
3. **Skill Creator** — writes a new `.py` skill to `app/tools/document_skills/`
4. **Regression Test** — auto-generates a pytest file
5. **Changelog** — appends an entry to `docs/evolutions/`

## Document Skills

Each format has a dedicated builder in `app/tools/document_skills/`:

| Builder | Format | Library |
|---|---|---|
| `docx_builder.py` | Word | python-docx |
| `pptx_builder.py` | PowerPoint | python-pptx |
| `xlsx_builder.py` | Excel | openpyxl |
| `pdf_builder.py` | PDF | reportlab |

The Designer calls these directly — no LLM code generation at runtime.
