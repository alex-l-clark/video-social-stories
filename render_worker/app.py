import os, tempfile, subprocess, shlex, json, gc
from typing import List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse

app = FastAPI(title="Render Worker")

def _run(cmd: str):
    proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", errors="ignore"))

@app.get("/health")
def health():
    try:
        # Check if ffmpeg is available
        result = subprocess.run(["ffmpeg", "-version"], 
                              capture_output=True, text=True, timeout=5)
        ffmpeg_ok = result.returncode == 0
        ffmpeg_version = result.stdout.split('\n')[0] if ffmpeg_ok else "Not available"
    except Exception as e:
        ffmpeg_ok = False
        ffmpeg_version = f"Error: {str(e)}"
    
    return {
        "ok": True,
        "ffmpeg_available": ffmpeg_ok,
        "ffmpeg_version": ffmpeg_version,
        "temp_dir": tempfile.gettempdir(),
        "memory_usage": f"{os.getpid()}"
    }

@app.post("/render")
async def render(
    scenes: str = Form(...),
    subs: UploadFile = File(...),
    # dynamic list of files image_{id}, audio_{id}
    files: List[UploadFile] = File(None),
):
    tmp = None
    try:
        scenes_meta = json.loads(scenes.replace("'", '"'))
    except Exception:
        try:
            scenes_meta = json.loads(scenes)
        except Exception:
            raise HTTPException(400, "invalid scenes json")

    tmp = tempfile.mkdtemp(prefix="render-worker-")
    try:
        # Save subs
        srt_path = os.path.join(tmp, "story.srt")
        with open(srt_path, "wb") as f:
            f.write(await subs.read())

        # Map of id to paths
        id_to_paths = {}
        for meta in scenes_meta:
            sid = meta["id"]
            id_to_paths[sid] = {"img": None, "aud": None, "dur": int(meta["duration_sec"]) }

        # Save files
        # The incoming UploadFiles are not labeled; instead, we rely on field names by FastAPI
        # But since we used a generic files: List[UploadFile], fallback to filename prefixes
        for uf in files or []:
            name = uf.filename
            data = await uf.read()
            if name.endswith(".png") or name.endswith(".jpg"):
                # expect name like scene_{id}.png
                base = os.path.splitext(name)[0]
                sid = int(base.split("_")[-1]) if "_" in base else None
                if sid in id_to_paths:
                    p = os.path.join(tmp, f"scene_{sid}.png")
                    with open(p, "wb") as f:
                        f.write(data)
                    id_to_paths[sid]["img"] = p
            elif name.endswith(".mp3"):
                base = os.path.splitext(name)[0]
                sid = int(base.split("_")[-1]) if "_" in base else None
                if sid in id_to_paths:
                    p = os.path.join(tmp, f"scene_{sid}.mp3")
                    with open(p, "wb") as f:
                        f.write(data)
                    id_to_paths[sid]["aud"] = p

        # Render per scene
        scene_outs = []
        for sid in sorted(id_to_paths.keys()):
            paths = id_to_paths[sid]
            if not paths["img"] or not paths["aud"]:
                raise HTTPException(400, f"missing files for scene {sid}")
            out = os.path.join(tmp, f"scene_{sid}.mp4")
            dur = max(1, paths["dur"])  # guard
            cmd = (
                f'ffmpeg -y -loop 1 -i {shlex.quote(paths["img"])} -i {shlex.quote(paths["aud"])} '
                f'-filter_complex "[0:v]scale=1280:720:flags=bilinear,format=yuv420p[v]" -map "[v]" -map 1:a '
                f'-c:v libx264 -preset ultrafast -crf 28 -pix_fmt yuv420p -r 30 -t {dur} '
                f'-c:a aac -b:a 96k -ac 2 -shortest -threads 1 -bufsize 512k '
                f'-max_muxing_queue_size 512 {shlex.quote(out)}'
            )
            _run(cmd)
            scene_outs.append(out)
            # Clean up scene files immediately to save memory
            try:
                os.remove(paths["img"])
                os.remove(paths["aud"])
                gc.collect()  # Force garbage collection after each scene
            except:
                pass

        # Concat
        list_path = os.path.join(tmp, "concat.txt")
        with open(list_path, "w") as f:
            for p in scene_outs:
                f.write(f"file '{p}'\n")
        tmp_concat = os.path.join(tmp, "tmp_concat.mp4")
        _run(f"ffmpeg -y -f concat -safe 0 -i {shlex.quote(list_path)} -c copy {shlex.quote(tmp_concat)}")

        # Burn subs with memory optimization
        final_path = os.path.join(tmp, "final.mp4")
        _run(f"ffmpeg -y -i {shlex.quote(tmp_concat)} -vf subtitles={shlex.quote(srt_path)} "
             f"-c:v libx264 -preset ultrafast -crf 28 -c:a copy -threads 1 -bufsize 512k "
             f"-max_muxing_queue_size 512 {shlex.quote(final_path)}")

        # Get file size first and validate it's not corrupted
        file_size = os.path.getsize(final_path)
        if file_size <= 1024:  # Less than 1KB is suspicious/corrupt
            raise RuntimeError(f"Generated video file is too small ({file_size} bytes), likely corrupted")
        
        # Read the entire file into memory to ensure it's complete before streaming
        with open(final_path, "rb") as f:
            video_data = f.read()
        
        # Verify the data is actually complete
        if len(video_data) != file_size:
            raise RuntimeError(f"File size mismatch: expected {file_size}, got {len(video_data)}")
        
        # Clean up temporary files before streaming
        try:
            shutil.rmtree(tmp, ignore_errors=True)
            tmp = None  # Mark as cleaned up
        except Exception as e:
            print(f"Warning: Could not clean up temp dir: {e}")
        
        def iterfile():
            # Stream from memory instead of file to avoid file handle issues
            chunk_size = 64 * 1024  # 64KB chunks
            for i in range(0, len(video_data), chunk_size):
                yield video_data[i:i + chunk_size]

        headers = {
            "Content-Disposition": 'attachment; filename="social-story.mp4"',
            "Content-Length": str(file_size)
        }
        return StreamingResponse(iterfile(), media_type="video/mp4", headers=headers)
        
    except Exception as e:
        # Clean up on error
        if tmp:
            try:
                import shutil
                shutil.rmtree(tmp, ignore_errors=True)
            except:
                pass
        raise HTTPException(500, str(e))
    finally:
        # Force garbage collection
        gc.collect()


