import os, uuid, tempfile, httpx, asyncio, shutil, logging
from langgraph.graph import StateGraph, END
from .models import OrchestrationState, StoryRequest, StorySpec, Scene
from .llm import get_story_spec
from .replicate_client import create_and_wait_image
from .elevenlabs_client import tts_to_bytes
from .media import write_bytes, write_text, build_srt_from_spec, ffmpeg_scene_clip, ffmpeg_concat, ffmpeg_burn_subs
from .settings import RENDER_WORKER_URL

logger = logging.getLogger(__name__)

def _mk_state(req: StoryRequest) -> OrchestrationState:
    job_id = str(uuid.uuid4())
    tmp_dir = os.path.join(tempfile.gettempdir(), "social-story", job_id)
    os.makedirs(tmp_dir, exist_ok=True)
    return OrchestrationState(job_id=job_id, tmp_dir=tmp_dir, request=req)

async def node_story_spec(state: OrchestrationState) -> OrchestrationState:
    logger.info(f"Generating story spec for job {state.job_id}")
    try:
        raw = get_story_spec(state.request)
        state.spec = StorySpec.model_validate(raw)
        write_text(os.path.join(state.tmp_dir, "story_spec.json"), state.spec.model_dump_json(indent=2))
        logger.info(f"Story spec generated with {len(state.spec.scenes)} scenes")
        return state
    except Exception as e:
        logger.error(f"Failed to generate story spec for job {state.job_id}: {str(e)}")
        raise

async def _scene_asset(scene: Scene, tmp_dir: str):
    logger.info(f"Generating assets for scene {scene.id}")
    
    # Image via Replicate
    logger.info(f"Requesting image from Replicate for scene {scene.id}")
    url = await create_and_wait_image(scene.image_prompt)
    logger.info(f"Got image URL from Replicate: {url}")
    
    async with httpx.AsyncClient() as client:
        img = await client.get(url)
        img.raise_for_status()
        img_path = os.path.join(tmp_dir, f"scene_{scene.id}.png")
        
        # Convert WebP to PNG if needed using Pillow
        try:
            from PIL import Image
            import io
            
            # Check if the image is WebP and convert to PNG
            image_data = img.content
            with Image.open(io.BytesIO(image_data)) as pil_img:
                if pil_img.format == 'WEBP':
                    logger.info(f"Converting WebP to PNG for scene {scene.id}")
                    # Convert RGBA to RGB if necessary to avoid transparency issues with ffmpeg
                    if pil_img.mode in ('RGBA', 'LA'):
                        # Create white background
                        background = Image.new('RGB', pil_img.size, (255, 255, 255))
                        if pil_img.mode == 'LA':
                            pil_img = pil_img.convert('RGBA')
                        background.paste(pil_img, mask=pil_img.split()[-1])  # Use alpha channel as mask
                        pil_img = background
                    elif pil_img.mode != 'RGB':
                        pil_img = pil_img.convert('RGB')
                    
                    # Save as PNG
                    png_buffer = io.BytesIO()
                    pil_img.save(png_buffer, format='PNG')
                    image_data = png_buffer.getvalue()
                    
        except ImportError:
            logger.warning("Pillow not available for image conversion, saving as-is")
        except Exception as e:
            logger.warning(f"Image conversion failed: {e}, saving as-is")
        
        write_bytes(img_path, image_data)
        logger.info(f"Saved image to {img_path}")
    
    # Audio via ElevenLabs
    logger.info(f"Requesting audio from ElevenLabs for scene {scene.id}")
    audio_bytes = await tts_to_bytes(scene.script)
    audio_path = os.path.join(tmp_dir, f"scene_{scene.id}.mp3")
    write_bytes(audio_path, audio_bytes)
    logger.info(f"Saved audio to {audio_path}")
    
    return img_path, audio_path

async def node_assets(state: OrchestrationState) -> OrchestrationState:
    assert state.spec
    total_scenes = len(state.spec.scenes)
    logger.info(f"Generating assets for {total_scenes} scenes")
    
    # Process scenes one at a time to avoid overwhelming the APIs
    for i, scene in enumerate(state.spec.scenes):
        logger.info(f"Processing scene {i+1}/{len(state.spec.scenes)}")
        try:
            img_path, audio_path = await _scene_asset(scene, state.tmp_dir)
            state.image_paths.append(img_path)
            state.audio_paths.append(audio_path)
            logger.info(f"Generated assets for scene {i}: image={os.path.exists(img_path)}, audio={os.path.exists(audio_path)}")
            
            # Small delay between scenes to be respectful to APIs
            if i < len(state.spec.scenes) - 1:  # Don't wait after the last scene
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error generating assets for scene {i}: {str(e)}")
            raise
    
    return state

async def node_render(state: OrchestrationState) -> OrchestrationState:
    assert state.spec
    logger.info(f"Starting video rendering for job {state.job_id}")
    srt_text = build_srt_from_spec(state.spec)
    srt_path = os.path.join(state.tmp_dir, "story.srt")
    write_text(srt_path, srt_text)
    logger.info(f"Created SRT file: {srt_path}")

    # If external render worker is configured, offload rendering
    if RENDER_WORKER_URL:
        import httpx
        logger.info(f"Using external render worker at {RENDER_WORKER_URL}")
        # Prepare payload: scene assets and metadata
        scenes_payload = []
        for sc in sorted(state.spec.scenes, key=lambda s: s.id):
            img = os.path.join(state.tmp_dir, f"scene_{sc.id}.png")
            aud = os.path.join(state.tmp_dir, f"scene_{sc.id}.mp3")
            scenes_payload.append({
                "id": sc.id,
                "duration_sec": sc.duration_sec,
                "image_path": img,
                "audio_path": aud,
            })
        # We will upload files as multipart form-data to the worker
        files = []
        try:
            for sc in scenes_payload:
                # Single 'files' field makes FastAPI receive as List[UploadFile]
                # Validate files exist and log sizes for debugging
                try:
                    img_size = os.path.getsize(sc['image_path'])
                    aud_size = os.path.getsize(sc['audio_path'])
                    logger.info(f"Scene {sc['id']} file sizes: image={img_size}B, audio={aud_size}B")
                except FileNotFoundError:
                    logger.error(f"Missing file(s) for scene {sc['id']}: img={os.path.exists(sc['image_path'])}, aud={os.path.exists(sc['audio_path'])}")
                files.append(("files", (f"scene_{sc['id']}.png", open(sc['image_path'], "rb"), "image/png")))
                files.append(("files", (f"scene_{sc['id']}.mp3", open(sc['audio_path'], "rb"), "audio/mpeg")))
            files.append(("subs", ("story.srt", open(srt_path, "rb"), "application/x-subrip")))
            import json
            scenes_data = json.dumps([{k: v for k, v in sc.items() if k in ("id", "duration_sec")} for sc in scenes_payload])
            # Send scenes as form data, not as a file
            form_data = {"scenes": scenes_data}
            async with httpx.AsyncClient(timeout=300) as client:
                out_path = os.path.join(state.tmp_dir, "final.mp4")
                # Stream the response to disk to avoid large memory usage and truncation issues
                async with client.stream("POST", f"{RENDER_WORKER_URL}/render", files=files, data=form_data) as resp:
                    if resp.status_code >= 400:
                        body_text = await resp.aread()
                        logger.error(
                            "Render worker failed: status=%s, body=%s, headers=%s",
                            resp.status_code,
                            body_text.decode("utf-8", errors="ignore"),
                            dict(resp.headers),
                        )
                        logger.warning("Render worker failed, falling back to local ffmpeg rendering")
                        raise Exception("Render worker failed, using fallback")

                    content_type = resp.headers.get("content-type", "")
                    if "video/mp4" not in content_type.lower():
                        # Read a small sample for logging and then fall back
                        preview = (await resp.aread())[:512]
                        logger.error("Unexpected worker content-type: %s, preview=%r", content_type, preview)
                        raise Exception("Render worker returned non-video content, using fallback")

                    with open(out_path, "wb") as f:
                        async for chunk in resp.aiter_bytes():
                            if chunk:
                                f.write(chunk)

                # Basic sanity check on resulting file size
                try:
                    file_size = os.path.getsize(out_path)
                except Exception:
                    file_size = 0
                if file_size <= 1024:  # Less than 1KB is suspicious/corrupt
                    logger.error("Worker video too small (%d bytes), falling back to local rendering", file_size)
                    raise Exception("Worker produced tiny file, using fallback")

                state.final_path = out_path
                logger.info(f"Received final video from worker: size={file_size} bytes")
                return state
        except Exception as e:
            logger.warning(f"External render worker failed: {e}. Falling back to local ffmpeg rendering.")
            # Fall through to local rendering below
        finally:
            # Close file handles
            for _, (_name, fh, _ctype) in files:
                try:
                    fh.close()
                except Exception:
                    pass

    # Fallback: local ffmpeg rendering (may not work on serverless)
    logger.warning("Attempting local ffmpeg fallback rendering")
    try:
        for sc in sorted(state.spec.scenes, key=lambda s: s.id):
            img = os.path.join(state.tmp_dir, f"scene_{sc.id}.png")
            aud = os.path.join(state.tmp_dir, f"scene_{sc.id}.mp3")
            out = os.path.join(state.tmp_dir, f"scene_{sc.id}.mp4")
            logger.info(f"Rendering scene {sc.id}: img={os.path.exists(img)}, audio={os.path.exists(aud)}")
            ffmpeg_scene_clip(img, aud, out, sc.duration_sec)
            state.scene_video_paths.append(out)

        tmp_concat = os.path.join(state.tmp_dir, "tmp_concat.mp4")
        ffmpeg_concat(state.scene_video_paths, tmp_concat)
        final_path = os.path.join(state.tmp_dir, "final.mp4")
        ffmpeg_burn_subs(tmp_concat, srt_path, final_path)
        state.final_path = final_path
        logger.info("Local ffmpeg rendering completed successfully")
        return state
    except Exception as ffmpeg_error:
        logger.error(f"Local ffmpeg rendering also failed: {ffmpeg_error}")
        # If both external worker and local ffmpeg fail, we need to raise an error
        raise RuntimeError("Both external render worker and local ffmpeg rendering failed. Please check the render worker service or run locally.")
    
    return state

def build_graph():
    g = StateGraph(OrchestrationState)
    g.add_node("story_spec", node_story_spec)
    g.add_node("assets", node_assets)
    g.add_node("render", node_render)
    g.set_entry_point("story_spec")
    g.add_edge("story_spec", "assets")
    g.add_edge("assets", "render")
    g.add_edge("render", END)
    return g.compile()

GRAPH = build_graph()

async def run_pipeline(req: StoryRequest) -> OrchestrationState:
    state = _mk_state(req)
    try:
        logger.info(f"Starting pipeline for job {state.job_id} in {state.tmp_dir}")
        final_state = await GRAPH.ainvoke(state)
        logger.info(f"Pipeline completed. Type: {type(final_state)}")
        logger.info(f"Final state keys: {list(final_state.keys()) if hasattr(final_state, 'keys') else 'No keys method'}")
        
        # Convert LangGraph's result back to our state object
        if hasattr(final_state, 'get'):
            # It's a dict-like object, convert back to OrchestrationState
            result_state = OrchestrationState(
                job_id=final_state.get("job_id", state.job_id),
                tmp_dir=final_state.get("tmp_dir", state.tmp_dir),
                request=final_state.get("request", state.request),
                spec=final_state.get("spec"),
                image_paths=final_state.get("image_paths", []),
                audio_paths=final_state.get("audio_paths", []),
                scene_video_paths=final_state.get("scene_video_paths", []),
                final_path=final_state.get("final_path")
            )
            logger.info(f"Converted final path: {result_state.final_path}")
            return result_state
        else:
            # It's already our state object
            logger.info(f"Final path: {final_state.final_path}")
            return final_state
    except Exception as e:
        logger.error(f"Pipeline failed for job {state.job_id}: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        # Cleanup on error
        shutil.rmtree(state.tmp_dir, ignore_errors=True)
        raise
