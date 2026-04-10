# AgentPress

**Brand-Aware Autonomous Document Creation Pipeline**

AgentPress is a 6-agent AI system that autonomously researches, drafts, formats, and quality-reviews enterprise documents — and when it fails, it writes its own code to fix itself.

Supports **PPTX · DOCX · XLSX · PDF** output with strict brand compliance enforcement.

---

## Pipeline Status

| Agent | Role | Status |
|---|---|---|
| 🧠 Orchestrator | Planning, spec generation, task decomposition | <span class="agent-badge active">Active</span> |
| 🔍 Researcher | RAG retrieval + Tavily web search | <span class="agent-badge active">Active</span> |
| ✍️ Synthesizer | Content drafting from research brief | <span class="agent-badge active">Active</span> |
| 🎨 Designer | Branded document building (PPTX/DOCX/XLSX/PDF) | <span class="agent-badge active">Active</span> |
| 🔬 Inspector | Two-stage QA: factual accuracy + brand compliance | <span class="agent-badge active">Active</span> |
| 🧬 Meta-Engineer | Self-improvement: writes new skills on failure | <span class="agent-badge active">Active</span> |

---

## How It Works

```
User Prompt
    │
    ▼
Orchestrator ──► Researcher ──► Synthesizer ──► Designer ──► Inspector
                                                                  │
                                              ┌── QA failed? ────┤
                                              │  retry           │ QA passed
                                              ▼                  ▼
                                           Designer            END / Download
                                              │
                                   max retries hit?
                                              ▼
                                       Meta-Engineer
                                    (writes new skill)
```

1. **Orchestrator** parses your prompt, detects output format, brainstorms a document spec, and breaks it into a task plan
2. **Researcher** queries the internal knowledge base (RAGFlow) and runs live web searches (Tavily) to compile a validated research brief
3. **Synthesizer** turns the research brief into structured document text
4. **Designer** calls deterministic skill scripts to build the final file with brand colors (`#1A1A2E` navy, `#E94560` crimson)
5. **Inspector** runs a two-stage QA review — Stage 1: factual accuracy, Stage 2: brand compliance
6. If QA fails after max retries, the **Meta-Engineer** writes a new Python skill to fix the root cause

---

## Output Formats

=== "DOCX"
    Word documents with branded headings, bullet lists, and Calibri font.
    Built with `python-docx`.

=== "PPTX"
    Presentations with navy background slides, crimson titles, and bullet content.
    Built with `python-pptx`.

=== "XLSX"
    Multi-sheet spreadsheets with pipe-table data, crimson column headers, and zebra striping.
    Built with `openpyxl`.

=== "PDF"
    Branded PDFs with a navy cover page, page headers/footers, and section headings.
    Built with `reportlab`.

---

## Brand Identity

| Token | Value | Usage |
|---|---|---|
| Primary (Navy) | `#1A1A2E` | Backgrounds, headings, table headers |
| Accent (Crimson) | `#E94560` | Section headings, bullets, accents |
| Off-white | `#EAEAEA` | Body text on dark backgrounds |
| Font | Calibri / Manrope | Documents / UI |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + LangGraph |
| Frontend | React + Vite + Tailwind CSS |
| LLM Provider | OpenRouter (Gemini 3 Flash) |
| Memory | ChromaDB + SQLite |
| Web Search | Tavily |
| Document Skills | python-docx, python-pptx, openpyxl, reportlab |
| Audit Trail | MkDocs Material → GitHub Pages |

---

## Audit Trail

- [Evolution Log](evolutions/index.md) — every skill the Meta-Engineer has written
- [Document Ledger](document_ledger/index.md) — log of all generated documents

---

*AgentPress — Autonomous Document Intelligence*
