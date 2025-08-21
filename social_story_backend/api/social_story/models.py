from pydantic import BaseModel, Field
from typing import List, Optional

class StoryRequest(BaseModel):
    age: int = 6
    reading_level: str = "early_reader"
    diagnosis_summary: str = "autism; prefers routine"
    situation: str
    setting: str
    words_to_avoid: List[str] = Field(default_factory=list)
    voice_preset: str = "calm_childlike_female"

class Scene(BaseModel):
    id: int
    goal: str
    script: str
    on_screen_text: str
    image_prompt: str
    duration_sec: int
    audio_ssml: str

class StorySpec(BaseModel):
    meta: dict
    scenes: List[Scene]
    closing_affirmation: str
    srt: str

class OrchestrationState(BaseModel):
    job_id: str
    tmp_dir: str
    request: StoryRequest
    spec: Optional[StorySpec] = None
    image_paths: List[str] = Field(default_factory=list)
    audio_paths: List[str] = Field(default_factory=list)
    scene_video_paths: List[str] = Field(default_factory=list)
    final_path: Optional[str] = None
