"""
app/api/routes.py — FastAPI endpoints for AgentPress
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, Dict
import uuid
import os
import json
import asyncio
from pathlib import Path
from datetime import datetime, timezone

from app.agents.graph import compiled_graph
from app.core.config import settings
from app.core.logger import setup_logger

log = setup_logger("api")
router = APIRouter()

# In-memory job store for MVP
jobs: Dict[str, Dict] = {}

OUTPUTS_DIR = Path(settings.OUTPUT_DIR)
SKILLS_REGISTRY = Path("app/tools/skills_registry.json")
BRAND_MD = Path("app/knowledge_base/brand.md")
USER_MD = Path("app/knowledge_base/user.md")
AGENT_LOG = Path("logs/agent_execution.log")


# ── Request models ─────────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = None
    output_format: Optional[str] = None  # pptx | docx | xlsx | pdf

class CorrectionRequest(BaseModel):
    original: str
    corrected: str
    session_id: str

class KnowledgeUpdateRequest(BaseModel):
    file: str  # "brand" | "user"
    content: str


# ── Core pipeline endpoints ────────────────────────────────────────────────────

@router.post("/generate")
async def generate_document(request: GenerateRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    session_id = request.session_id or str(uuid.uuid4())

    jobs[job_id] = {
        "job_id": job_id,
        "session_id": session_id,
        "status": "queued",
        "current_node": None,
        "file_path": None,
        "error": None,
        "prompt": request.prompt,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "qa_retry_count": 0,
        "evolution_triggered": False,
    }

    background_tasks.add_task(run_pipeline, job_id, session_id, request.prompt)
    return {"job_id": job_id, "session_id": session_id, "status": "queued"}


@router.get("/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


@router.post("/submit-correction")
async def submit_correction(request: CorrectionRequest):
    try:
        inputs = {
            "session_id": request.session_id,
            "correction_original": request.original,
            "correction_edited": request.corrected,
            "evolution_triggered": True,
        }
        for event in compiled_graph.stream(inputs):
            pass
        return {"status": "correction_processed", "session_id": request.session_id}
    except Exception as e:
        log.error(f"Correction submission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Jobs history ───────────────────────────────────────────────────────────────

@router.get("/jobs")
async def list_jobs():
    """Return all jobs sorted by creation time descending."""
    sorted_jobs = sorted(
        jobs.values(),
        key=lambda j: j.get("created_at", ""),
        reverse=True,
    )
    return {"jobs": sorted_jobs, "total": len(sorted_jobs)}


# ── Outputs / Data Room ────────────────────────────────────────────────────────

@router.get("/outputs")
async def list_outputs():
    """List all generated files in the outputs directory."""
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    files = []
    for f in sorted(OUTPUTS_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if f.is_file():
            stat = f.stat()
            files.append({
                "name": f.name,
                "path": str(f),
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                "extension": f.suffix.lstrip("."),
            })
    return {"files": files, "total": len(files)}


@router.get("/outputs/download/{filename}")
async def download_output(filename: str):
    """Download a generated output file."""
    file_path = OUTPUTS_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    # Prevent path traversal
    if not file_path.resolve().is_relative_to(OUTPUTS_DIR.resolve()):
        raise HTTPException(status_code=403, detail="Access denied")
    return FileResponse(path=str(file_path), filename=filename)


# ── Skill Library ──────────────────────────────────────────────────────────────

@router.get("/skills")
async def list_skills():
    """Return the skills registry plus static tool categories."""
    registry = []
    if SKILLS_REGISTRY.exists():
        try:
            registry = json.loads(SKILLS_REGISTRY.read_text())
        except Exception:
            registry = []

    # Also enumerate static skills from tools directories
    static_skills = []
    tools_root = Path("app/tools")
    for category in ["document_skills", "research_skills", "superpowers"]:
        cat_dir = tools_root / category
        if cat_dir.exists():
            for f in cat_dir.glob("*.py"):
                if f.name == "__init__.py":
                    continue
                static_skills.append({
                    "filename": f.name,
                    "category": category,
                    "path": str(f),
                    "type": "static",
                })

    return {
        "auto_generated": registry,
        "static": static_skills,
        "total": len(registry) + len(static_skills),
    }


# ── Knowledge Base (Settings) ──────────────────────────────────────────────────

@router.get("/knowledge")
async def get_knowledge():
    """Return brand.md and user.md content."""
    return {
        "brand": BRAND_MD.read_text(encoding="utf-8") if BRAND_MD.exists() else "",
        "user": USER_MD.read_text(encoding="utf-8") if USER_MD.exists() else "",
    }


@router.post("/knowledge")
async def update_knowledge(request: KnowledgeUpdateRequest):
    """Update brand.md or user.md."""
    if request.file == "brand":
        BRAND_MD.write_text(request.content, encoding="utf-8")
    elif request.file == "user":
        USER_MD.write_text(request.content, encoding="utf-8")
    else:
        raise HTTPException(status_code=400, detail="file must be 'brand' or 'user'")
    return {"status": "updated", "file": request.file}


# ── Analytics ─────────────────────────────────────────────────────────────────

@router.get("/analytics")
async def get_analytics():
    """Aggregate stats from the in-memory job store."""
    total = len(jobs)
    completed = sum(1 for j in jobs.values() if j["status"] == "completed")
    failed = sum(1 for j in jobs.values() if j["status"] == "failed")
    processing = sum(1 for j in jobs.values() if j["status"] == "processing")
    evolutions = sum(1 for j in jobs.values() if j.get("evolution_triggered"))
    avg_retries = (
        sum(j.get("qa_retry_count", 0) for j in jobs.values()) / total if total else 0
    )

    # Count evolutions from docs/evolutions/
    evolutions_dir = Path("docs/evolutions")
    evolution_logs = list(evolutions_dir.glob("*.md")) if evolutions_dir.exists() else []

    return {
        "total_jobs": total,
        "completed": completed,
        "failed": failed,
        "processing": processing,
        "queued": total - completed - failed - processing,
        "qa_pass_rate": round(completed / total * 100, 1) if total else 0,
        "avg_qa_retries": round(avg_retries, 2),
        "evolution_count": len(evolution_logs),
        "evolution_triggered_jobs": evolutions,
    }


# ── Log streaming (Agent Swarm Chat) ──────────────────────────────────────────

@router.get("/logs/stream")
async def stream_logs():
    """SSE stream of agent_execution.log for the Agent Swarm Chat screen."""
    async def event_generator():
        AGENT_LOG.parent.mkdir(parents=True, exist_ok=True)
        if not AGENT_LOG.exists():
            AGENT_LOG.touch()

        with open(AGENT_LOG, "r", encoding="utf-8") as f:
            # Send existing lines first
            for line in f:
                line = line.strip()
                if line:
                    yield f"data: {json.dumps({'line': line})}\n\n"
            # Then tail for new lines
            while True:
                line = f.readline()
                if line:
                    line = line.strip()
                    if line:
                        yield f"data: {json.dumps({'line': line})}\n\n"
                else:
                    await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── Pipeline runner ────────────────────────────────────────────────────────────

@router.post("/restart")
async def restart_server(background_tasks: BackgroundTasks):
    """
    Kill both backend and frontend processes and relaunch via start.py.
    """
    import sys, os, asyncio
    from pathlib import Path

    async def _do_restart():
        await asyncio.sleep(0.5)  # Let the response send first

        pid_file = Path(".pids")
        if pid_file.exists():
            # Kill the frontend (Vite) process
            try:
                pids = pid_file.read_text().strip().splitlines()
                if len(pids) >= 2:
                    ui_pid = int(pids[1])
                    os.kill(ui_pid, 9)
            except Exception as e:
                log.warning(f"Could not kill UI process: {e}")

        # Re-exec this process — uvicorn hot-reload handles the backend restart
        os.execv(sys.executable, [sys.executable] + sys.argv)

    background_tasks.add_task(_do_restart)
    return {"status": "restarting"}
    log.info(f"Starting pipeline for job {job_id}")
    jobs[job_id]["status"] = "processing"

    inputs = {
        "user_prompt": prompt,
        "session_id": session_id,
        "job_id": job_id,
    }

    try:
        for event in compiled_graph.stream(inputs):
            for node, state in event.items():
                log.info(f"Node '{node}' finished.")
                jobs[job_id]["current_node"] = node
                jobs[job_id]["qa_retry_count"] = state.get("qa_retry_count", 0)
                jobs[job_id]["evolution_triggered"] = state.get("evolution_triggered", False)
                if state.get("formatted_file_path"):
                    jobs[job_id]["file_path"] = state["formatted_file_path"]
                if state.get("qa_report"):
                    jobs[job_id]["qa_report"] = state["qa_report"]

        jobs[job_id]["status"] = "completed"
        log.info(f"Pipeline finished for job {job_id}")
    except Exception as e:
        log.error(f"Pipeline error for job {job_id}: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
