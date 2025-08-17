import os, subprocess, shlex
from typing import List
from .models import StorySpec
from .settings import VIDEO_WIDTH, VIDEO_HEIGHT, FPS

def write_bytes(path: str, data: bytes):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)

def write_text(path: str, text: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def build_srt_from_spec(spec: StorySpec) -> str:
    return spec.srt

def ffmpeg_scene_clip(img_path: str, audio_path: str, out_path: str, duration: int, w=VIDEO_WIDTH, h=VIDEO_HEIGHT, fps=FPS):
    d_frames = duration * fps
    cmd = (
        f'ffmpeg -y -loop 1 -i {shlex.quote(img_path)} -i {shlex.quote(audio_path)} '
        f'-filter_complex "[0:v]zoompan=z=\'min(zoom+0.0008,1.08)\':d={d_frames}:s={w}x{h},format=yuv420p[v]" '
        f'-map "[v]" -map 1:a -c:v libx264 -pix_fmt yuv420p -r {fps} -t {duration} -c:a aac -shortest {shlex.quote(out_path)}'
    )
    _run(cmd)

def ffmpeg_concat(scene_files: List[str], out_tmp_path: str):
    list_path = out_tmp_path.replace(".mp4", "_concat.txt")
    with open(list_path, "w") as f:
        for p in scene_files:
            f.write(f"file '{p}'\n")
    cmd = f"ffmpeg -y -f concat -safe 0 -i {shlex.quote(list_path)} -c copy {shlex.quote(out_tmp_path)}"
    _run(cmd)

def ffmpeg_burn_subs(in_path: str, srt_path: str, out_path: str):
    cmd = f"ffmpeg -y -i {shlex.quote(in_path)} -vf subtitles={shlex.quote(srt_path)} -c:a copy {shlex.quote(out_path)}"
    _run(cmd)

def _run(cmd: str):
    print(f"Running FFmpeg command: {cmd}")
    proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        error_msg = proc.stderr.decode("utf-8", errors="ignore")
        print(f"FFmpeg command failed with return code {proc.returncode}")
        print(f"Error output: {error_msg}")
        raise RuntimeError(f"FFmpeg failed: {error_msg}")
    else:
        print("FFmpeg command completed successfully")
