# Advanced Brand-Aware Autonomous Document Creation Pipeline

## Overview
A 5-agent, self-improving AI system designed for enterprise-level document generation. It integrates specific open-weight models with state-of-the-art orchestration, memory, and retrieval frameworks, strictly governed by the Superpowers methodology for engineering discipline.

## Core Tech Stack & Frameworks

* **Langflow (The Nervous System):** Visual pipeline orchestration for routing state and subagents.
* **Hermes & Claude-mem (The Brain):** Handles procedural memory, user models, and context compression.
* **RAGFlow (The Engine):** Deep document understanding for the internal Brand Knowledge Base.
* **Agent Reach (The Scavenger):** Autonomous live-web crawling for external market data.
* **Awesome-Claude-Skills (The Toolbelt):** Execution scripts (`xlsx`, `canvas-design`).
* **Superpowers (The Discipline):** Enforces Test-Driven Development (TDD), systematic debugging, and subagent isolation to prevent "vibe coding" and hallucinations.

---

## Agent Team Architecture

| Department | Agent Role | Assigned Model | Core Responsibility | Tech Integration |
| :--- | :--- | :--- | :--- | :--- |
| **Orchestration** | **The Lead Orchestrator** | `openai/gpt-oss-120b:free` | Parses prompts, handles `brainstorming`, writes task plans, and routes state. | **Hermes**, **Claude-mem**, & **Superpowers** (`writing-plans`) |
| **Research** | **The Researcher** | `nvidia/nemotron-nano-12b-v2-vl:free` | Ingests dense files and gathers raw data, running as an isolated subagent. | **RAGFlow** & **Agent Reach** |
| **Production** | **The Content Synthesizer** | `meta-llama/llama-3.2-3b-instruct:free` | Drafts the narrative based *strictly* on the approved task plan. | N/A (Standard LLM generation) |
| **Production** | **The Brand & Format Specialist** | `qwen/qwen3-coder:free-coding` | Writes execution code to compile documents using strict TDD methodology. | **Awesome-Claude-Skills** & **Superpowers** (`TDD`) |
| **Quality Assurance**| **The Compliance Inspector**| `qwen/qwen3-next-80b-a3b:free` | Reviews outputs using a two-stage spec compliance check. | **Superpowers** (`systematic-debugging`) |

---

## Execution Workflow

1.  **Intake & Brainstorming:** User submits a prompt. The **Lead Orchestrator** loads context via **Claude-mem** and uses the **Superpowers** `brainstorming` skill to finalize a Document Spec.
2.  **Task Planning:** The Orchestrator uses `writing-plans` to break the spec into isolated tasks.
3.  **Retrieval (Subagent):** **Langflow** spins up the **Researcher** with only its specific task. It queries **RAGFlow** for internal data and **Agent Reach** for external data.
4.  **Drafting (Subagent):** Validated data routes to the **Content Synthesizer** to create the text.
5.  **Formatting (TDD):** The text passes to the **Format Specialist**. It triggers **Awesome-Claude-Skills** scripts while adhering to the **Superpowers** `RED-GREEN-REFACTOR` testing cycle to guarantee brand compliance in the final file.
6.  **Quality Control:** The **Compliance Inspector** runs a two-stage review. If an error is found, it uses `systematic-debugging` to trace the root cause and loops back to Production.
7.  **Memory Update:** Manual human edits update the **Hermes** brand model for future sessions.