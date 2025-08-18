import os, shutil
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

# Ensure .env is loaded before importing modules that initialize API clients
from .settings import has_all_keys, ALLOWED_ORIGINS
from .models import StoryRequest
from .orchestrator import run_pipeline
from typing import Optional
import asyncio
from .utils import safe_open_binary

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Social Story Backend (MVP)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    keys_ok = has_all_keys()
    logger.info(f"Health check: API keys present = {keys_ok}")
    return {"ok": True, "has_keys": keys_ok}

@app.post("/v1/social-story:render")
async def render_story(req: StoryRequest):
    # Deprecated: keep for local/manual use. Prefer async job flow below.
    if not req.situation or not req.setting:
        raise HTTPException(400, "situation and setting are required")
    final_state = await run_pipeline(req)
    # Handle LangGraph's AddableValuesDict result
    final_path = final_state.get("final_path") if hasattr(final_state, 'get') else final_state.final_path
    tmp_dir = final_state.get("tmp_dir") if hasattr(final_state, 'get') else final_state.tmp_dir
    job_id = final_state.get("job_id") if hasattr(final_state, 'get') else final_state.job_id
    
    if not final_path or not os.path.exists(final_path):
        raise HTTPException(500, "Failed to render video")
    def iterfile(path, tmp_dir):
        try:
            with safe_open_binary(path) as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    yield chunk
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
    filename = f"social-story-{job_id}.mp4"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(
        iterfile(final_path, tmp_dir),
        media_type="video/mp4",
        headers=headers
    )

# --- Simple in-memory job registry for async workflow ---
JOBS = {}

class JobRecord:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.status = "queued"  # queued -> running -> succeeded/failed
        self.error: Optional[str] = None
        self.tmp_dir: Optional[str] = None
        self.final_path: Optional[str] = None

async def _background_render(job: JobRecord, req: StoryRequest):
    try:
        logger.info(f"Starting background render for job {job.job_id}")
        job.status = "running"
        final_state = await run_pipeline(req)
        # Handle LangGraph's AddableValuesDict result
        job.tmp_dir = final_state.get("tmp_dir") if hasattr(final_state, 'get') else final_state.tmp_dir
        job.final_path = final_state.get("final_path") if hasattr(final_state, 'get') else final_state.final_path
        job.status = "succeeded"
        logger.info(f"Background render completed successfully for job {job.job_id}")
    except Exception as e:
        logger.error(f"Background render failed for job {job.job_id}: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        job.error = str(e)
        job.status = "failed"
        if job.tmp_dir:
            shutil.rmtree(job.tmp_dir, ignore_errors=True)

@app.post("/v1/social-story:start")
async def start_job(req: StoryRequest):
    logger.info(f"Starting job for situation: {req.situation[:50]}...")
    
    # Validate API keys are present
    if not has_all_keys():
        logger.error("API keys missing, cannot start job")
        raise HTTPException(500, "Server configuration error: missing required API keys")
    
    if not req.situation or not req.setting:
        raise HTTPException(400, "situation and setting are required")
    
    # Create a placeholder state to get job_id and tmp_dir semantics
    # We rely on run_pipeline to generate a unique job_id; for API we generate here
    job_id = os.urandom(16).hex()
    job = JobRecord(job_id)
    JOBS[job_id] = job

    # If running on Vercel serverless, background tasks will not survive
    # after the HTTP response is returned. To avoid the "running forever"
    # symptom, run the pipeline synchronously here as a pragmatic hotfix.
    if os.getenv("VERCEL") == "1":
        logger.info(f"VERCEL=1 detected. Running job {job_id} synchronously in this request.")
        try:
            job.status = "running"
            final_state = await run_pipeline(req)
            job.tmp_dir = final_state.get("tmp_dir") if hasattr(final_state, 'get') else final_state.tmp_dir
            job.final_path = final_state.get("final_path") if hasattr(final_state, 'get') else final_state.final_path
            job.status = "succeeded"
            logger.info(f"Synchronous run completed for job {job_id}")
        except Exception as e:
            job.error = str(e)
            job.status = "failed"
            logger.error(f"Synchronous run failed for job {job_id}: {e}")
            if job.tmp_dir:
                shutil.rmtree(job.tmp_dir, ignore_errors=True)
        return {"job_id": job_id, "status": job.status, "error": job.error}

    logger.info(f"Created job {job_id}, starting background processing")
    asyncio.create_task(_background_render(job, req))
    return {"job_id": job_id, "status": job.status}

@app.get("/v1/jobs/{job_id}")
def job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return {"job_id": job.job_id, "status": job.status, "error": job.error}

@app.get("/v1/jobs/{job_id}/download")
def job_download(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    if job.status != "succeeded" or not job.final_path or not os.path.exists(job.final_path):
        raise HTTPException(409, "job not ready")
    def iterfile(path, tmp_dir):
        try:
            with safe_open_binary(path) as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    yield chunk
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            JOBS.pop(job_id, None)
    filename = f"social-story-{job.job_id}.mp4"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(
        iterfile(job.final_path, job.tmp_dir or os.path.dirname(job.final_path)),
        media_type="video/mp4",
        headers=headers
    )
