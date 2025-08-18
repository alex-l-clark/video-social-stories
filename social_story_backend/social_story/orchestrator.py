import os, uuid, tempfile, httpx, asyncio, shutil, logging
from langgraph.graph import StateGraph, END
from .models import OrchestrationState, StoryRequest, StorySpec, Scene
from .llm import get_story_spec
from .replicate_client import create_and_wait_image
from .elevenlabs_client import tts_to_bytes
from .media import write_bytes, write_text, build_srt_from_spec, ffmpeg_scene_clip, ffmpeg_concat, ffmpeg_burn_subs

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
        write_bytes(img_path, img.content)
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
    # In serverless, keep work bounded to avoid timeouts
    serverless = (os.getenv("VERCEL") is not None) or os.getenv("VERCEL_URL") or os.getenv("NOW_REGION") or os.getenv("SERVERLESS") == "1"
    max_scenes = min(total_scenes, 2) if serverless else total_scenes
    logger.info(f"Generating assets for {total_scenes} scenes (processing {max_scenes}{' due to serverless limits' if serverless else ''})")
    
    # Process scenes one at a time to avoid overwhelming the APIs
    for i, scene in enumerate(state.spec.scenes[:max_scenes]):
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

    # Per-scene render
    for sc in sorted(state.spec.scenes, key=lambda s: s.id):
        img = os.path.join(state.tmp_dir, f"scene_{sc.id}.png")
        aud = os.path.join(state.tmp_dir, f"scene_{sc.id}.mp3")
        out = os.path.join(state.tmp_dir, f"scene_{sc.id}.mp4")
        logger.info(f"Rendering scene {sc.id}: img={os.path.exists(img)}, audio={os.path.exists(aud)}")
        ffmpeg_scene_clip(img, aud, out, sc.duration_sec)
        if os.path.exists(out):
            logger.info(f"Scene {sc.id} video created successfully: {out}")
        else:
            logger.error(f"Scene {sc.id} video creation FAILED: {out}")
        state.scene_video_paths.append(out)

    # Concat + burn subs
    tmp_concat = os.path.join(state.tmp_dir, "tmp_concat.mp4")
    logger.info(f"Concatenating {len(state.scene_video_paths)} scene videos")
    ffmpeg_concat(state.scene_video_paths, tmp_concat)
    logger.info(f"Concatenation completed: {os.path.exists(tmp_concat)}")
    
    final_path = os.path.join(state.tmp_dir, "final.mp4")
    logger.info(f"Burning subtitles into final video")
    ffmpeg_burn_subs(tmp_concat, srt_path, final_path)
    logger.info(f"Final video created: {os.path.exists(final_path)}")
    state.final_path = final_path
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
