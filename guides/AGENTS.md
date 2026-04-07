# Brand-Aware Autonomous Document Creation Pipeline

## Overview
This document outlines the architecture for a 5-agent, self-improving AI system designed for enterprise-level document generation. The system leverages specialized open-weight models from OpenRouter to handle distinct phases of research, drafting, programmatic formatting, and quality assurance.

## Core Capabilities
* **Agentic Workflow:** Autonomous planning, execution, and review.
* **Self-Improving Memory:** Feedback loops to update internal context and avoid repeated errors.
* **Brand Awareness:** Strict adherence to company guidelines, tones, hex codes, and templates.
* **Multi-Modal Support:** `skills.sh` execution layer for interacting with `.pdf`, `.docx`, `.xlsx`, and `.pptx` files.

---

## Agent Team Architecture

| Department | Agent Role | Assigned Model | Core Responsibility |
| :--- | :--- | :--- | :--- |
| **Orchestration & Memory** | **The Lead Orchestrator** | `openai/gpt-oss-120b:free` | Acts as the manager. Parses user prompts, delegates tasks, routes state between agents, and updates the memory vector database based on user feedback. |
| **Research & Data** | **The Researcher** | `nvidia/nemotron-nano-12b-v2-vl:free-doc analysis` | The `autoresearch` wing. Ingests dense PDFs, parses spreadsheets, and analyzes charts to extract validated raw data. |
| **Production** | **The Content Synthesizer** | `meta-llama/llama-3.2-3b-instruct:free-languages or voice` | The writer. Takes raw data and drafts the narrative, focusing purely on language, structure, and logical flow. |
| **Production** | **The Brand & Format Specialist** | `qwen/qwen3-coder:free-coding` | The designer/developer. Writes the execution code (e.g., via `python-docx` or `pptx`) to inject brand hex codes, logos, and compile the final document. |
| **Quality Assurance** | **The Compliance Inspector** | `qwen/qwen3-next-80b-a3b-instruct:free-code QA` | The gatekeeper. Reviews code execution and written content for factual accuracy and strict brand compliance before final output. |

---

## Execution Workflow

1. **Intake:** User submits a prompt to the **Lead Orchestrator**.
2. **Retrieval:** The Orchestrator tasks the **Researcher** to gather necessary data from internal files or web sources using the `skills.sh` toolset.
3. **Drafting:** Extracted data is passed to the **Content Synthesizer** to create the raw text draft.
4. **Formatting:** The draft is passed to the **Brand & Format Specialist**, which writes the programmatic scripts to build the document and apply brand assets.
5. **Review:** The compiled file and code are reviewed by the **Compliance Inspector**. 
    * *If failed:* Routed back to Production for corrections.
    * *If passed:* Delivered to the user.
6. **Improvement:** Any human edits to the final document are logged by the Orchestrator into the system's memory for future tasks.