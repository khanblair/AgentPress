"""
app/api/routes.py — FastAPI endpoints for AgentPress
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict
import uuid

from app.agents.graph import compiled_graph
from app.core.logger import setup_logger

log = setup_logger("api")
router = APIRouter()

# In-memory job store for MVP
jobs: Dict[str, Dict] = {}

class GenerateRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = None

class CorrectionRequest(BaseModel):
    original: str
    corrected: str
    session_id: str

@router.post("/generate")
async def generate_document(request: GenerateRequest, background_tasks: BackgroundTasks):
    """
    Trigger the LangGraph pipeline asynchronously.
    """
    job_id = str(uuid.uuid4())
    session_id = request.session_id or str(uuid.uuid4())
    
    jobs[job_id] = {"status": "starting", "job_id": job_id, "session_id": session_id}
    
    background_tasks.add_task(run_pipeline, job_id, session_id, request.prompt)
    
    return {"job_id": job_id, "session_id": session_id, "status": "queued"}

@router.get("/status/{job_id}")
async def get_status(job_id: str):
    """
    Get the current status of a generation job.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]

@router.post("/submit-correction")
async def submit_correction(request: CorrectionRequest):
    """
    Submit a human correction to trigger the evolution engine.
    """
    # Simply trigger the meta-engineer with the correction details
    try:
        inputs = {
            "session_id": request.session_id,
            "correction_original": request.original,
            "correction_edited": request.corrected,
            "evolution_triggered": True
        }
        # Run only the meta_engineer node from the graph
        # This is a shortcut for the correction loop
        for event in compiled_graph.stream(inputs):
            pass # We only care about the side effects to knowledge_base/brand.md
            
        return {"status": "correction_processed", "session_id": request.session_id}
    except Exception as e:
        log.error(f"Correction submission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_pipeline(job_id: str, session_id: str, prompt: str):
    """
    Executes the LangGraph pipeline and updates the job status.
    """
    log.info(f"Starting pipeline for job {job_id}")
    jobs[job_id]["status"] = "processing"
    
    inputs = {
        "user_prompt": prompt,
        "session_id": session_id,
        "job_id": job_id
    }
    
    try:
        # Full LangGraph execution
        for event in compiled_graph.stream(inputs):
            # Log progress for internal tracking
            for node, state in event.items():
                log.info(f"Node '{node}' finished.")
                jobs[job_id]["current_node"] = node
                if state.get("formatted_file_path"):
                    jobs[job_id]["file_path"] = state["formatted_file_path"]

        jobs[job_id]["status"] = "completed"
        log.info(f"Pipeline finished for job {job_id}")
    except Exception as e:
        log.error(f"Pipeline error for job {job_id}: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
