"""
AgentPress — FastAPI Entry Point
Brand-Aware Autonomous Document Creation Pipeline
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logger import setup_logger
from app.api.routes import router

logger = setup_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: setup and teardown."""
    logger.info("AgentPress starting up...")
    logger.info(f"Environment: {settings.APP_ENV}")
    yield
    logger.info("AgentPress shutting down.")


app = FastAPI(
    title="AgentPress",
    description="Brand-Aware Autonomous Document Creation Pipeline — 6-Agent AI System",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow local Streamlit UI and any future Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8501", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "AgentPress",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
