# Project Implementation: GitHub Repository Integration

## 1. Langflow (The Nervous System)
* **MVP:** Use Langflow Docker/Desktop to visually map OpenRouter models. Connect your frontend to the Langflow API endpoint.
* **Advancement:** Move to Model Context Protocol (MCP) to run the visual graphs as modular, headless tools in Python.

## 2. RAGFlow (Internal Brand Knowledge Base)
* **MVP:** Use RAGFlow for deep document understanding of company guidelines, PDFs, and Excel templates. Connect to the Researcher agent (`Nemotron-12B`).
* **Advancement:** Implement template-based chunking for specific file types (.pptx vs .pdf) to optimize retrieval speed and accuracy.

## 3. Agent Reach (External Research)
* **MVP:** Use CLI wrappers for YouTube, Reddit, and Twitter. Grant the Researcher agent shell access to pull live market trends without API fees.
* **Advancement:** Containerize the execution environment to ensure secure, read-only shell access for the LLM.

## 4. Awesome-Claude-Skills (Execution Toolbelt)
* **MVP:** Adopt the `SKILL.md` and `scripts/` folder structure. Use pre-vetted skills for Excel and PowerPoint manipulation.
* **Advancement:** Create a "Skill-Creator" agent to autonomously write new reusable skills from technical documentation.

## 5. Claude-Mem (Session Memory)
* **MVP:** Use SQLite and MCP tools (`search`, `timeline`, `observations`) to manage context and recall user preferences from past sessions.
* **Advancement:** Integrate Chroma Vector Database for hybrid semantic search and "Endless Mode" for long-term project persistence.

## 6. Hermes Agent (Brand Modeling)
* **MVP:** Use persistent `USER.md` and `BRAND.md` files for the Orchestrator to read. Manually append user corrections to these files.
* **Advancement:** Implement Cognitive Encoding to resolve memory contradictions and MemoryScope to isolate narrative vs. visual memories.