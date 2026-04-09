# AgentPress

A brand-aware autonomous document creation pipeline powered by a 6-agent AI system. AgentPress researches, drafts, formats, and quality-reviews enterprise documents — and when it fails, it writes its own code to fix itself.

Supports **PPTX**, **DOCX**, **XLSX**, and **PDF** output with strict brand compliance enforcement.

---

## What It Does

You submit a prompt like *"Create a Q3 market analysis presentation"* and AgentPress:

1. Plans a document spec and task breakdown
2. Gathers data from your knowledge base and the web
3. Drafts the content
4. Builds the formatted file with brand colors and fonts
5. Runs a two-stage QA review (factual accuracy + brand compliance)
6. If QA keeps failing — writes a new Python skill to fix the root cause

The entire execution is visible in real-time through the React UI, and every evolution is logged to a GitHub Pages audit trail.

---

## Architecture

```
FastAPI (Python) + LangGraph  ←→  React + Vite (UI)
         │
    ┌────┴────────────────────────────────────┐
    │              LangGraph Pipeline          │
    │                                          │
    │  Orchestrator → Researcher → Synthesizer │
    │       → Designer → Inspector             │
    │              ↕ (retry loop)              │
    │          Meta-Engineer (evolution)       │
    └──────────────────────────────────────────┘
         │
    ChromaDB (memory) + SQLite (sessions)
    RAGFlow (optional) + Tavily (web search)
```

**Backend:** FastAPI, LangGraph, ChromaDB, OpenRouter  
**Frontend:** React, Vite, TanStack Query, Tailwind CSS  
**Document Skills:** python-docx, python-pptx, openpyxl, reportlab  
**Audit Trail:** MkDocs → GitHub Pages

---

## The 6 Agents

| Agent | Role |
|---|---|
| **Orchestrator** | Parses the user prompt, brainstorms a document spec, decomposes it into a task plan, and routes state through the pipeline |
| **Researcher** | Queries the internal knowledge base (RAGFlow) and runs live web searches (Tavily) to compile a validated research brief |
| **Synthesizer** | Turns the research brief into structured document text — no formatting, just clean content |
| **Designer** | Calls deterministic skill scripts to build the final file with brand colors (`#1A1A2E`, `#E94560`) and Calibri font |
| **Inspector** | Runs a two-stage QA: Stage 1 checks factual accuracy against research data, Stage 2 checks brand compliance |
| **Meta-Engineer** | Triggered when QA fails after max retries — writes a new Python skill to fix the root cause and registers it for future runs |

The pipeline is a LangGraph `StateGraph`. After the Inspector, routing is conditional:

```
Inspector
  ├── QA passed + no evolution needed → END
  ├── QA passed + evolution flagged   → Meta-Engineer → END
  ├── QA failed + retries remaining   → Designer (retry)
  └── QA failed + max retries hit     → Meta-Engineer → END
```

---

## Evolution Engine

When the pipeline hits a wall, the Meta-Engineer kicks in:

- **Delta Parser** — diffs AI output vs. human corrections to classify the error type (`brand_visual`, `brand_tone`, `factual`, `structure`)
- **Rule Resolver** — appends persistent rules to `brand.md` or `user.md`; marks older conflicting rules as `[SUPERSEDED]`
- **Skill Creator** — writes a new `.py` skill to `app/tools/document_skills/` with a controlled API (only allowed directories)
- **Regression Test** — auto-generates a pytest file to prevent the same failure from recurring
- **Changelog** — publishes a markdown entry to `docs/evolutions/` for the audit trail

---

## Skills System

Skills are deterministic Python scripts for document manipulation — no LLM code generation at runtime.

```
app/skills/
├── docx/          # Word: pack/unpack XML, accept changes, comments
├── pptx/          # PowerPoint: add slides, clean, thumbnail, pack/unpack
├── xlsx/          # Excel: pack/unpack, recalculate formulas
├── pdf/           # PDF: fill forms, extract fields, convert to images
└── skill-creator/ # Meta: benchmark, evaluate, and package new skills
```

The Designer reads `app/tools/skills_registry.json` to discover available skills. Auto-generated skills from the Meta-Engineer are registered there automatically.

To create a new skill manually:

```
my-skill/
├── SKILL.md          # Frontmatter: name, description, triggers
├── scripts/          # Executable Python scripts
└── references/       # Supporting docs and templates
```

---

## Memory

- **ChromaDB** — persistent vector database at `./data/chromadb` for semantic memory across sessions
- **SessionMemory** — retrieves relevant past interactions to give the Orchestrator context
- **Knowledge Base** — two markdown files the agents read on every run:
  - `app/knowledge_base/brand.md` — visual and tonal rules (colors, fonts, tone of voice)
  - `app/knowledge_base/user.md` — user preferences, updated dynamically from corrections

---

## API Reference

All endpoints are prefixed with `/api/v1`.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/generate` | Submit a document request (returns `job_id`) |
| `GET` | `/status/{job_id}` | Poll job status and agent progress |
| `POST` | `/submit-correction` | Submit human feedback to trigger evolution |
| `GET` | `/jobs` | List all jobs |
| `GET` | `/outputs` | List generated files |
| `GET` | `/outputs/download/{filename}` | Download a generated file |
| `GET` | `/outputs/preview/{filename}` | Extract structured content for preview |
| `POST` | `/outputs/chat` | Chat with a document (Q&A or edit requests) |
| `GET` | `/skills` | List all available skills |
| `GET` | `/knowledge` | Get `brand.md` and `user.md` content |
| `POST` | `/knowledge` | Update `brand.md` or `user.md` |
| `GET` | `/analytics` | Pipeline metrics (pass rate, retries, evolutions) |
| `GET` | `/logs/stream` | SSE stream of live agent execution logs |
| `GET` | `/chat/messages` | Get global agent chat history |
| `POST` | `/chat/message` | Send a message — `@mention` an agent to get a response |

Interactive API docs available at `http://localhost:8000/docs`.

---

## UI Pages

| Page | Route | Description |
|---|---|---|
| Main Workspace | `/` | Submit prompts and view recent jobs |
| Active Pipeline | `/pipeline/:jobId` | Real-time agent execution with live status |
| Document Review | `/review` | Preview, edit, and chat with generated documents |
| Agent Chat | `/chat` | Group chat room — `@mention` any agent |
| Skill Library | `/skills` | Browse static and auto-generated skills |
| Data Room | `/data-room` | Manage knowledge base files |
| Analytics | `/analytics` | QA pass rates, retry counts, evolution stats |
| Settings | `/settings` | Configure environment and preferences |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- An [OpenRouter](https://openrouter.ai) API key
- (Optional) [Tavily](https://tavily.com) API key for web search
- (Optional) [RAGFlow](https://ragflow.io) for internal document retrieval

### Installation

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd agentpress

# 2. Set up Python environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Set up the frontend
cd ui/web
npm install
cd ../..

# 4. Configure environment
cp .env .env.local               # Edit with your keys
```

### Environment Variables

```env
# Required
OPENROUTER_API_KEY=sk-or-v1-...
MODEL=google/gemini-3-flash-preview   # Any OpenRouter model

# Database (auto-created)
CHROMA_DB_PATH=./data/chromadb
SQLITE_DB_PATH=./data/sessions.db

# Optional — web search
TAVILY_API_KEY=tvly-...

# Optional — internal document retrieval
RAGFLOW_API_URL=http://localhost:9380
RAGFLOW_API_KEY=your_key_here

# App settings
APP_ENV=development
LOG_LEVEL=DEBUG
MAX_QA_RETRIES=3
OUTPUT_DIR=./outputs
```

### Running

```bash
# Start both backend and frontend together
npm run dev
```

Or manually in separate terminals:

```bash
# Terminal 1 — Backend (port 8000)
.venv/bin/uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend (port 3000)
cd ui/web && npm run dev
```

Then open `http://localhost:3000`.

---

## Project Structure

```
agentpress/
├── main.py                          # FastAPI entry point
├── requirements.txt                 # Python dependencies
├── package.json                     # Concurrently scripts (npm run dev)
│
├── app/
│   ├── agents/                      # The 6 LangGraph agents
│   │   ├── state.py                 # Shared TypedDict pipeline state
│   │   ├── graph.py                 # LangGraph StateGraph definition
│   │   ├── orchestrator.py          # Agent 1: Planning & spec
│   │   ├── researcher.py            # Agent 2: Data gathering
│   │   ├── synthesizer.py           # Agent 3: Content drafting
│   │   ├── designer.py              # Agent 4: Document formatting
│   │   ├── inspector.py             # Agent 5: QA & compliance
│   │   ├── meta_engineer.py         # Agent 6: Self-improvement
│   │   ├── messenger.py             # In-memory agent message bus
│   │   └── client.py                # OpenRouter LLM client
│   │
│   ├── api/
│   │   └── routes.py                # All FastAPI endpoints
│   │
│   ├── core/
│   │   ├── config.py                # Pydantic settings from .env
│   │   └── logger.py                # Loguru-based structured logging
│   │
│   ├── evolution_engine/            # Self-improvement system
│   │   ├── delta_parser.py          # Diff AI output vs. human corrections
│   │   ├── rule_resolver.py         # Update brand.md / user.md
│   │   └── skill_creator.py         # Controlled skill file writer
│   │
│   ├── memory/
│   │   ├── vector_db.py             # ChromaDB wrapper
│   │   └── session.py               # Session context retrieval
│   │
│   ├── knowledge_base/
│   │   ├── brand.md                 # Brand rules (colors, fonts, tone)
│   │   └── user.md                  # User preferences (auto-updated)
│   │
│   ├── skills/                      # Deterministic document skill packages
│   │   ├── docx/
│   │   ├── pptx/
│   │   ├── xlsx/
│   │   ├── pdf/
│   │   └── skill-creator/
│   │
│   └── tools/
│       ├── document_skills/         # PPTX, DOCX, XLSX, PDF builders
│       ├── research_skills/         # Web scrapers, Reddit CLI
│       ├── superpowers/             # Brainstorm, writing plans, debug logic
│       └── skills_registry.json     # Auto-updated skill index
│
├── ui/web/                          # React + Vite frontend
│   └── src/
│       ├── pages/                   # All UI pages
│       ├── components/              # Shared components
│       ├── api/                     # API client
│       └── constants/               # Agent definitions
│
├── docs/                            # MkDocs audit trail (→ GitHub Pages)
│   └── evolutions/                  # Auto-generated evolution changelogs
│
├── tests/                           # Pytest suite + auto-generated regression tests
├── logs/                            # Agent execution and error logs
└── outputs/                         # Generated documents
```

---

## Audit Trail

Every pipeline run and evolution is logged. The `docs/` folder is published to GitHub Pages via `.github/workflows/pages.yml` using MkDocs Material.

To build the docs locally:

```bash
mkdocs serve
```

---

## Testing

```bash
# Run the full test suite
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=term-missing
```

Auto-generated regression tests from the Meta-Engineer live in `tests/test_evolution_*.py`.

---

## Brand Configuration

Edit `app/knowledge_base/brand.md` to set your brand rules, or update it live via the Settings page or `POST /api/v1/knowledge`.

Default brand palette used by the Designer:

| Token | Value |
|---|---|
| Primary (Navy) | `#1A1A2E` |
| Accent (Crimson) | `#E94560` |
| Background | `#EAEAEA` |
| Font | Calibri |

---

## License

See individual skill packages in `app/skills/*/LICENSE.txt` for third-party licensing. Core pipeline code is proprietary.
