import os, shutil
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import uuid
import tempfile

# Ensure .env is loaded before importing modules that initialize API clients
from .settings import has_all_keys, ALLOWED_ORIGINS
from .models import StoryRequest, StorySpec
from .orchestrator import run_pipeline
from .kv_storage import kv
from .llm import get_story_spec
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

# --- KV-based job registry for scalable async workflow ---
async def create_job_record(job_id: str, request: StoryRequest) -> dict:
    """Create a new job record in KV storage"""
    job_data = {
        "job_id": job_id,
        "status": "queued",
        "error": None,
        "request": request.model_dump(),
        "created_at": str(asyncio.get_event_loop().time()),
        "spec": None,
        "scenes_completed": 0,
        "total_scenes": 0,
        "final_path": None
    }
    await kv.set_job(job_id, job_data)
    return job_data

async def get_job_record(job_id: str) -> Optional[dict]:
    """Get job record from KV storage or fallback to in-memory"""
    job_data = await kv.get_job(job_id)
    if job_data:
        return job_data
    
    # Fallback to in-memory for backward compatibility
    return JOBS.get(job_id)

# Legacy in-memory storage for fallback
JOBS = {}

class JobRecord:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.status = "queued"
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
    
    # Generate job ID and create KV record
    job_id = str(uuid.uuid4())
    job_data = await create_job_record(job_id, req)
    
    # Start the async pipeline - this will process step by step using webhooks
    asyncio.create_task(start_story_generation(job_id, req))
    
    return {"job_id": job_id, "status": "queued"}

async def start_story_generation(job_id: str, req: StoryRequest):
    """Start the story generation pipeline with KV state management"""
    try:
        # Update status to running
        await kv.update_job_status(job_id, "running")
        
        # Step 1: Generate story spec
        logger.info(f"Generating story spec for job {job_id}")
        raw_spec = get_story_spec(req)
        spec = StorySpec.model_validate(raw_spec)
        
        # Store spec in KV
        await kv.update_job_status(job_id, "running", 
                                   spec=spec.model_dump(), 
                                   total_scenes=len(spec.scenes),
                                   current_step="generating_assets")
        
        # Step 2: Generate assets for each scene
        logger.info(f"Starting asset generation for {len(spec.scenes)} scenes")
        await process_all_scenes(job_id, spec)
        
    except Exception as e:
        logger.error(f"Story generation failed for job {job_id}: {e}")
        await kv.update_job_status(job_id, "failed", error=str(e))

async def process_all_scenes(job_id: str, spec: StorySpec):
    """Process all scenes asynchronously"""
    # Start all scene processing concurrently (but with delays to respect API limits)
    tasks = []
    for i, scene in enumerate(spec.scenes):
        # Add small delays between requests to be respectful to APIs
        delay = i * 2  # 2 second delay between each scene start
        task = asyncio.create_task(process_scene_with_delay(job_id, scene, delay))
        tasks.append(task)
    
    # Wait for all scenes to complete
    await asyncio.gather(*tasks, return_exceptions=True)
    
    # Check if all scenes completed successfully
    job_data = await kv.get_job(job_id)
    if job_data and job_data.get("scenes_completed", 0) >= len(spec.scenes):
        # All scenes done - proceed to video rendering
        await render_final_video(job_id, spec)

async def process_scene_with_delay(job_id: str, scene, delay: int):
    """Process a single scene with initial delay"""
    if delay > 0:
        await asyncio.sleep(delay)
    
    logger.info(f"Processing scene {scene.id} for job {job_id}")
    
    try:
        # This will trigger Replicate and ElevenLabs in parallel
        # We'll use webhooks to track completion
        await initiate_scene_assets(job_id, scene)
    except Exception as e:
        logger.error(f"Failed to initiate scene {scene.id} for job {job_id}: {e}")
        await kv.update_job_status(job_id, "failed", error=str(e))

async def initiate_scene_assets(job_id: str, scene):
    """Initiate asset generation for a scene (placeholder for webhook implementation)"""
    # For now, keep the direct API calls but we'll add webhook support next
    from .replicate_client import create_and_wait_image
    from .elevenlabs_client import tts_to_bytes
    import httpx
    
    # Generate image
    image_url = await create_and_wait_image(scene.image_prompt)
    await kv.set_scene_asset(job_id, scene.id, "image", image_url)
    
    # Generate audio
    audio_bytes = await tts_to_bytes(scene.script)
    # For now, we'll need to store audio bytes differently - will implement blob storage
    
    # Update scene completion count
    job_data = await kv.get_job(job_id)
    if job_data:
        scenes_completed = job_data.get("scenes_completed", 0) + 1
        await kv.update_job_status(job_id, "running", scenes_completed=scenes_completed)

async def render_final_video(job_id: str, spec: StorySpec):
    """Render the final video once all assets are ready"""
    logger.info(f"Starting final video render for job {job_id}")
    await kv.update_job_status(job_id, "running", current_step="rendering_video")
    
    # This is a placeholder - we'll implement the video rendering
    # For now, just mark as completed
    await kv.update_job_status(job_id, "succeeded", current_step="completed")

@app.get("/v1/jobs/{job_id}")
async def job_status(job_id: str):
    job_data = await get_job_record(job_id)
    if not job_data:
        raise HTTPException(404, "job not found")
    
    # Handle both dict (KV) and JobRecord (legacy) formats
    if isinstance(job_data, dict):
        return {
            "job_id": job_data["job_id"],
            "status": job_data["status"],
            "error": job_data.get("error"),
            "progress": {
                "current_step": job_data.get("current_step", "unknown"),
                "scenes_completed": job_data.get("scenes_completed", 0),
                "total_scenes": job_data.get("total_scenes", 0)
            }
        }
    else:
        # Legacy JobRecord format
        return {"job_id": job_data.job_id, "status": job_data.status, "error": job_data.error}

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
