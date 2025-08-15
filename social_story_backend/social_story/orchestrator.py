import os, uuid, tempfile, httpx, asyncio, shutil
from langgraph.graph import StateGraph, END
from .models import OrchestrationState, StoryRequest, StorySpec, Scene
from .llm import get_story_spec
from .replicate_client import create_and_wait_image
from .elevenlabs_client import tts_to_bytes
from .media import write_bytes, write_text, build_srt_from_spec, ffmpeg_scene_clip, ffmpeg_concat, ffmpeg_burn_subs

def _mk_state(req: StoryRequest) -> OrchestrationState:
    job_id = str(uuid.uuid4())
    tmp_dir = os.path.join(tempfile.gettempdir(), "social-story", job_id)
    os.makedirs(tmp_dir, exist_ok=True)
    return OrchestrationState(job_id=job_id, tmp_dir=tmp_dir, request=req)

async def node_story_spec(state: OrchestrationState) -> OrchestrationState:
    raw = get_story_spec(state.request)
    state.spec = StorySpec.model_validate(raw)
    write_text(os.path.join(state.tmp_dir, "story_spec.json"), state.spec.model_dump_json(indent=2))
    return state

async def _scene_asset(scene: Scene, tmp_dir: str):
    # Image via Replicate
    url = await create_and_wait_image(scene.image_prompt)
    async with httpx.AsyncClient() as client:
        img = await client.get(url)
        img.raise_for_status()
        img_path = os.path.join(tmp_dir, f"scene_{scene.id}.png")
        write_bytes(img_path, img.content)
    # Audio via ElevenLabs
    audio_bytes = await tts_to_bytes(scene.script)
    audio_path = os.path.join(tmp_dir, f"scene_{scene.id}.mp3")
    write_bytes(audio_path, audio_bytes)
    return img_path, audio_path

async def node_assets(state: OrchestrationState) -> OrchestrationState:
    assert state.spec
    tasks = [_scene_asset(s, state.tmp_dir) for s in state.spec.scenes]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for r in results:
        if isinstance(r, Exception):
            raise r
        img_path, audio_path = r
        state.image_paths.append(img_path)
        state.audio_paths.append(audio_path)
    return state

async def node_render(state: OrchestrationState) -> OrchestrationState:
    assert state.spec
    srt_text = build_srt_from_spec(state.spec)
    srt_path = os.path.join(state.tmp_dir, "story.srt")
    write_text(srt_path, srt_text)

    # Per-scene render
    for sc in sorted(state.spec.scenes, key=lambda s: s.id):
        img = os.path.join(state.tmp_dir, f"scene_{sc.id}.png")
        aud = os.path.join(state.tmp_dir, f"scene_{sc.id}.mp3")
        out = os.path.join(state.tmp_dir, f"scene_{sc.id}.mp4")
        ffmpeg_scene_clip(img, aud, out, sc.duration_sec)
        state.scene_video_paths.append(out)

    # Concat + burn subs
    tmp_concat = os.path.join(state.tmp_dir, "tmp_concat.mp4")
    ffmpeg_concat(state.scene_video_paths, tmp_concat)
    final_path = os.path.join(state.tmp_dir, "final.mp4")
    ffmpeg_burn_subs(tmp_concat, srt_path, final_path)
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
        final_state = await GRAPH.ainvoke(state)
        return final_state
    except Exception:
        # Cleanup on error
        shutil.rmtree(state.tmp_dir, ignore_errors=True)
        raise
