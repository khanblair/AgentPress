"""
app/agents/researcher.py — Agent 2: The Researcher
Model: nvidia/nemotron-nano-12b-v2-vl:free (via OpenRouter)

Responsibilities:
 - Query RAGFlow for internal brand/template data
 - Call Agent Reach research_skills CLI tools for live web data
 - Return raw_research (validated data dump) + source lists
"""

import json
from openai import OpenAI
import requests

from app.agents.state import AgentState
from app.core.config import settings
from app.core.logger import setup_logger
from app.tools.research_skills.web_scraper import scrape_urls
from app.tools.research_skills.reddit_cli import fetch_reddit_trends

log = setup_logger("researcher")

client = OpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url=settings.OPENROUTER_BASE_URL,
)


def _query_ragflow(query: str) -> tuple[str, list[str]]:
    """Query RAGFlow API for internal brand knowledge."""
    if not settings.RAGFLOW_API_URL or not settings.RAGFLOW_API_KEY:
        log.warning("RAGFlow not configured — skipping internal retrieval.")
        return "", []
    try:
        resp = requests.post(
            f"{settings.RAGFLOW_API_URL}/v1/retrieval",
            headers={"Authorization": f"Bearer {settings.RAGFLOW_API_KEY}"},
            json={"query": query, "top_k": 5},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        chunks = data.get("chunks", [])
        text = "\n\n".join(c.get("content", "") for c in chunks)
        ids = [c.get("chunk_id", "") for c in chunks]
        return text, ids
    except Exception as e:
        log.error(f"RAGFlow query failed: {e}")
        return "", []


def run_researcher(state: AgentState) -> AgentState:
    log.info("Researcher: Starting data gathering phase.")

    task_plan = state.get("task_plan", [])
    document_spec = state.get("document_spec", "")
    search_query = document_spec[:500]  # Use spec as search seed

    # 1. Internal RAG retrieval
    rag_text, rag_sources = _query_ragflow(search_query)
    log.info(f"Researcher: Retrieved {len(rag_sources)} RAG chunks.")

    # 2. External web data via research_skills
    web_text = ""
    web_sources = []
    try:
        reddit_data = fetch_reddit_trends(query=search_query, limit=5)
        web_text += reddit_data.get("text", "")
        web_sources.extend(reddit_data.get("urls", []))
    except Exception as e:
        log.warning(f"Reddit fetch failed: {e}")

    # 3. Synthesise all data with the Researcher model
    synthesis_prompt = f"""You are a research analyst. Your task:
Synthesise the following raw data into a clean, factual research brief 
that will be used to write a document.

DOCUMENT SPEC:
{document_spec}

INTERNAL BRAND DATA (RAG):
{rag_text or "No internal data retrieved."}

EXTERNAL WEB DATA:
{web_text or "No external data retrieved."}

TASK PLAN:
{json.dumps(task_plan, indent=2)}

OUTPUT: A structured, bullet-pointed research brief. Be concise and factual.
Do NOT write the document — only provide validated data and facts."""

    log.debug(f"Researcher: Calling {settings.RESEARCHER_MODEL}.")
    response = client.chat.completions.create(
        model=settings.RESEARCHER_MODEL,
        messages=[{"role": "user", "content": synthesis_prompt}],
        temperature=0.1,
    )
    raw_research = response.choices[0].message.content.strip()
    log.info("Researcher: raw_research compiled.")

    return {
        **state,
        "raw_research": raw_research,
        "rag_sources": rag_sources,
        "web_sources": web_sources,
    }
