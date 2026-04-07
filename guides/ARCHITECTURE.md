# Project Architecture: Self-Evolving Brand-Aware Agent Pipeline

## Overview
This repository contains a 6-agent microservice architecture built with **FastAPI** and **LangGraph**. It autonomously researches, drafts, formats, and reviews enterprise documents. Crucially, it features an **Evolution Engine** (allowing the AI to write its own code to fix recurring bugs) and an automated **Audit Trail** (publishing its logs to a live GitHub Pages dashboard via MkDocs).

---

## 📂 The Master Directory Tree

```text
brand-agent-pipeline/
├── .github/
│   └── workflows/
│       └── pages.yml         # CI/CD pipeline: Auto-publishes the docs/ folder to GitHub Pages
│
├── .venv/                    # Python virtual environment (ignored in git)
├── .env                      # OpenRouter keys, DB URIs, and environment variables
├── mkdocs.yml                # Configuration and styling for the Audit Trail web dashboard
├── requirements.txt          # Python dependencies (FastAPI, LangGraph, MkDocs, etc.)
├── main.py                   # The backend entry point (FastAPI server)
│
├── docs/                     # 🌐 THE AUDIT TRAIL (Published to GitHub Pages)
│   ├── index.md              # Dashboard homepage
│   ├── evolutions/           # Auto-generated changelogs when Agent 6 writes new code
│   └── document_ledger/      # Logs of generated files, API costs, and QA reports
│
├── ui/                       # 💻 THE PYTHON FRONTEND
│   ├── app.py                # Streamlit or Gradio UI (for testing before Next.js integration)
│   └── components/           # Reusable UI elements
│
├── logs/                     # 📝 PERSISTENT SYSTEM LOGS
│   ├── agent_execution.log   # Raw terminal outputs, reasoning, and test results
│   └── api_errors.log        # FastAPI server errors
│
├── app/                      # 🧠 THE AI CORE
│   ├── api/                  # The HTTP Bridge to the UI
│   │   ├── __init__.py
│   │   └── routes.py         # Endpoints (e.g., POST /generate, POST /submit-correction)
│   │
│   ├── core/                 # App Configuration
│   │   ├── __init__.py
│   │   ├── config.py         # Loads .env and global settings
│   │   └── logger.py         # Routes AI terminal outputs to the /logs directory
│   │
│   ├── agents/               # Live State & Orchestration (LangGraph)
│   │   ├── __init__.py
│   │   ├── state.py          # The schema defining data passed between agents (Redux-style)
│   │   ├── graph.py          # The visual map connecting agents and defining fallback loops
│   │   ├── orchestrator.py   # Agent 1 (120B): Planner & State Router
│   │   ├── researcher.py     # Agent 2 (12B VL): Data Gatherer (RAG + Web Search)
│   │   ├── synthesizer.py    # Agent 3 (3B): Content Writer
│   │   ├── designer.py       # Agent 4 (Qwen Coder): Formatter (TDD code execution)
│   │   ├── inspector.py      # Agent 5 (80B): QA & Systematic Debugging
│   │   └── meta_engineer.py  # Agent 6 (Qwen Coder): Writes new scripts to fix failures
│   │
│   ├── evolution_engine/     # 🧬 THE SELF-IMPROVEMENT LOOP
│   │   ├── __init__.py
│   │   ├── delta_parser.py   # Compares AI output vs. Human corrections to find errors
│   │   ├── skill_creator.py  # Logic allowing Agent 6 to create files in app/tools/
│   │   └── rule_resolver.py  # Updates brand.md and resolves memory contradictions
│   │
│   ├── tools/                # 🛠️ THE SKILL REGISTRY (Executable Python Scripts)
│   │   ├── __init__.py
│   │   ├── document_skills/  # Output generators (e.g., pptx_builder.py, csv_builder.py)
│   │   ├── research_skills/  # Web scrapers and CLI wrappers (Agent Reach)
│   │   └── superpowers/      # Strict logic for Brainstorming, Planning, and Debugging
│   │
│   ├── memory/               # 💾 CONTEXT MANAGEMENT (Hermes / Claude-mem)
│   │   ├── __init__.py
│   │   ├── vector_db.py      # Connection to local ChromaDB or pgvector
│   │   └── session.py        # Compresses and retrieves past user interactions
│   │
│   └── knowledge_base/       # 📚 RAG INTERNAL DATA
│       ├── brand.md          # Immutable visual/tonal rules
│       ├── user.md           # Dynamically updated user preferences
│       └── templates/        # Base .pptx or .docx files for the Designer to manipulate
│
└── tests/                    # 🛡️ SUPERPOWERS TDD (Test-Driven Development)
    ├── __init__.py
    ├── test_formatting.py    # Ensures the Designer applied the correct brand hex codes
    ├── test_hallucinations.py# Ensures Researcher data matches RAG sources
    └── test_evolutions.py    # Auto-written tests by Agent 6 to prevent regression