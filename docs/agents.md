# Agent Reference

AgentPress uses a 6-agent LangGraph pipeline. Each agent has a single responsibility and communicates through the shared `AgentState`.

---

## 🧠 Orchestrator

**Role:** Strategic planning and task decomposition

- Detects output format from the user prompt (`pptx`, `docx`, `xlsx`, `pdf`)
- Loads brand context from `app/knowledge_base/brand.md` and user preferences from `user.md`
- Retrieves relevant past session context from ChromaDB
- Brainstorms a structured **Document Specification** using the `build_brainstorm_prompt` superpower
- Breaks the spec into an ordered **Task Plan** using `build_task_plan`
- Derives a human-readable filename slug (e.g. `q3-market-analysis-report_a1b2c3d4.docx`)

**Model:** `google/gemini-3-flash-preview` via OpenRouter

---

## 🔍 Researcher

**Role:** Data gathering and research synthesis

- Queries **RAGFlow** for internal brand/document knowledge (if configured)
- Runs live web searches via **Tavily** (falls back to Reddit CLI if not configured)
- Synthesizes all raw data into a concise, bullet-pointed research brief
- Never invents facts — only uses validated retrieved data

**Model:** `google/gemini-3-flash-preview` via OpenRouter

---

## ✍️ Synthesizer

**Role:** Content drafting

- Receives the document spec, task plan, and research brief
- Writes the complete document text following the task plan exactly
- Format-aware output:
    - **DOCX/PDF:** `## Section Title` headings + paragraphs + bullet points
    - **PPTX:** `## Slide N: Title` + bullet points
    - **XLSX:** Pipe-delimited table rows (`Col A | Col B | Col C`)
- Never applies visual formatting — that's the Designer's job

**Model:** `google/gemini-3-flash-preview` via OpenRouter

---

## 🎨 Designer

**Role:** Branded document building

Calls deterministic skill scripts — no LLM code generation at runtime:

| Format | Builder | Brand Applied |
|---|---|---|
| DOCX | `docx_builder.py` | Navy headings, crimson accents, Calibri font |
| PPTX | `pptx_builder.py` | Navy background, crimson titles, off-white text |
| XLSX | `xlsx_builder.py` | Navy section headers, crimson column headers, zebra rows |
| PDF | `pdf_builder.py` | Navy cover page, crimson headings, page headers/footers |

Brand colors: `#1A1A2E` (navy) · `#E94560` (crimson) · `#EAEAEA` (off-white)

---

## 🔬 Inspector

**Role:** Two-stage quality assurance

**Stage 1 — Factual Accuracy**

Checks every claim in the draft against the validated research data. Flags hallucinations.

**Stage 2 — Brand Compliance**

Verifies brand colors, fonts, and layout against `brand.md` guidelines.

Both stages end with `QA_VERDICT: PASS` or `QA_VERDICT: FAIL`. The overall QA passes only if both stages pass AND the file was built successfully (`tdd_passed: true`).

On failure, runs systematic debugging via `build_debug_prompt` to trace the root cause.

**Model:** `google/gemini-3-flash-preview` via OpenRouter

---

## 🧬 Meta-Engineer

**Role:** Self-improvement — triggered when QA fails after max retries

1. Parses the correction delta (if human feedback was provided)
2. Updates `brand.md` or `user.md` with persistent rule changes
3. Writes a new Python skill to `app/tools/document_skills/`
4. Auto-generates a regression test in `tests/`
5. Publishes a changelog entry to `docs/evolutions/`

The new skill is registered in `app/tools/skills_registry.json` and available for future runs.

**Model:** `google/gemini-3-flash-preview` via OpenRouter

---

## Pipeline Routing

```
orchestrator → researcher → synthesizer → designer → inspector
                                                          │
                                     ┌── QA failed ───────┤
                                     │  (retry < max)     │ QA passed
                                     ▼                    ▼
                                  designer              END
                                     │
                          max retries hit
                                     ▼
                              meta_engineer → END
```

The `MAX_QA_RETRIES` setting (default: `3`) controls how many times the Designer→Inspector loop runs before escalating to the Meta-Engineer.
