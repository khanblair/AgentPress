"""
app/core/config.py — Global settings loaded from .env
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    # ── App ───────────────────────────────────────────────────────────
    APP_ENV: str = Field(default="development")
    LOG_LEVEL: str = Field(default="INFO")
    MAX_QA_RETRIES: int = Field(default=3)
    OUTPUT_DIR: str = Field(default="./outputs")

    # ── OpenRouter ────────────────────────────────────────────────────
    OPENROUTER_API_KEY: str = Field(default="")
    OPENROUTER_BASE_URL: str = Field(default="https://openrouter.ai/api/v1")

    # ── Agent Models ──────────────────────────────────────────────────
    ORCHESTRATOR_MODEL: str = Field(default="openai/gpt-oss-120b:free")
    RESEARCHER_MODEL: str = Field(default="nvidia/nemotron-nano-12b-v2-vl:free")
    SYNTHESIZER_MODEL: str = Field(default="meta-llama/llama-3.2-3b-instruct:free")
    DESIGNER_MODEL: str = Field(default="qwen/qwen3-coder:free")
    INSPECTOR_MODEL: str = Field(default="qwen/qwen3-235b-a22b:free")
    META_ENGINEER_MODEL: str = Field(default="qwen/qwen3-coder:free")

    # ── Database ──────────────────────────────────────────────────────
    CHROMA_DB_PATH: str = Field(default="./data/chromadb")
    SQLITE_DB_PATH: str = Field(default="./data/sessions.db")

    # ── External Services ─────────────────────────────────────────────
    RAGFLOW_API_URL: str = Field(default="http://localhost:9380")
    RAGFLOW_API_KEY: str = Field(default="")
    LANGFLOW_API_URL: str = Field(default="http://localhost:7860")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
