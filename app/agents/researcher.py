"""
app/agents/researcher.py — Agent 2: The Researcher
Skill: Data gathering, RAG retrieval, research synthesis
"""

import json
import requests
from app.agents.state import AgentState
from app.agents.client import chat
from app.core.config import settings
from app.core.logger import setup_logger
from app.tools.research_skills.web_scraper import scrape_urls
from app.tools.research_skills.reddit_cli import fetch_reddit_trends

log = setup_logger("researcher")

SYSTEM_PROMPT = """You are the Researcher for AgentPress, an autonomous document pipeline.
Your role is data gathering and research synthesis.
You produce concise, bullet-pointed research briefs from raw data.
You are factual, precise, and never invent statistics.
Never write the document — only provide validated data and facts."""


def _query_ragflow(query: str) -> tuple[str, list[str]]:
    if not settings.RAGFLOW_API_URL or not settings.RAGFLOW_API_KEY:
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
        return "\n\n".join(c.get("content", "") for c in chunks), [c.get("chunk_id", "") for c in chunks]
    except Exception as e:
        log.error(f"RAGFlow query failed: {e}")
        return "", []


def run_researcher(state: AgentState) -> AgentState:
    log.info("Researcher: Starting data gathering phase.")

    task_plan     = state.get("task_plan", [])
    document_spec = state.get("document_spec", "")
    search_query  = document_spec[:500]

    rag_text, rag_sources = _query_ragflow(search_query)
    log.info(f"Researcher: Retrieved {len(rag_sources)} RAG chunks.")

    web_text, web_sources = "", []
    try:
        reddit_data = fetch_reddit_trends(query=search_query, limit=5)
        web_text = reddit_data.get("text", "")
        web_sources = reddit_data.get("urls", [])
    except Exception as e:
        log.warning(f"Reddit fetch failed: {e}")

    synthesis_prompt = f"""Synthesise the following raw data into a clean, factual research brief.

DOCUMENT SPEC:
{document_spec}

INTERNAL BRAND DATA (RAG):
{rag_text or "No internal data retrieved."}

EXTERNAL WEB DATA:
{web_text or "No external data retrieved."}

TASK PLAN:
{json.dumps(task_plan, indent=2)}

OUTPUT: A structured, bullet-pointed research brief. Be concise and factual."""

    log.debug(f"Researcher: Calling {settings.MODEL}.")
    raw_research = chat(SYSTEM_PROMPT, synthesis_prompt, temperature=0.1, max_tokens=512)
    if not raw_research:
        log.warning("Researcher: model returned empty content, using placeholder.")
        raw_research = "No research data available."
    log.info("Researcher: raw_research compiled.")

    return {
        **state,
        "raw_research": raw_research,
        "rag_sources": rag_sources,
        "web_sources": web_sources,
    }
