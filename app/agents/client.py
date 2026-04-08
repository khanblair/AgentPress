"""
app/agents/client.py — Shared OpenAI client for all agents.

All agents use the same model (settings.MODEL) via OpenRouter.
Role differentiation is handled through system prompts, not model selection.
"""

from openai import OpenAI
from app.core.config import settings

client = OpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url=settings.OPENROUTER_BASE_URL,
)


def chat(system_prompt: str, user_prompt: str, temperature: float = 0.3, max_tokens: int = 1024) -> str:
    """
    Single call wrapper used by all agents.
    Returns the text content, handling None gracefully.
    """
    response = client.chat.completions.create(
        model=settings.MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    choice = response.choices[0]
    return (
        choice.message.content
        or getattr(choice.message, "reasoning", None)
        or ""
    ).strip()
