#!/usr/bin/env python3
"""
Debug script to test the render worker with the same format the backend uses
"""
import httpx
import json
import asyncio

async def test_render_worker():
    """Test the render worker with the same format the backend uses"""
    
    # Test data - same as smoke test
    scenes_data = json.dumps([{"id": 1, "duration_sec": 1}])
    
    # Prepare files exactly like the backend does
    files = []
    
    # Add image and audio files
    with open("render_worker/tmp_smoke/scene_1.png", "rb") as f:
        files.append(("files", ("scene_1.png", f.read(), "image/png")))
    
    with open("render_worker/tmp_smoke/scene_1.mp3", "rb") as f:
        files.append(("files", ("scene_1.mp3", f.read(), "audio/mpeg")))
    
    # Add SRT file
    with open("render_worker/tmp_smoke/story.srt", "rb") as f:
        files.append(("subs", ("story.srt", f.read(), "application/x-subrip")))
    
    # Form data
    form_data = {"scenes": scenes_data}
    
    print(f"Sending request to render worker...")
    print(f"Scenes data: {scenes_data}")
    print(f"Files: {[f[1][0] for f in files]}")
    
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                "https://social-story-renderer.fly.dev/render", 
                files=files, 
                data=form_data
            )
            
            print(f"Response status: {resp.status_code}")
            print(f"Response headers: {dict(resp.headers)}")
            
            if resp.status_code == 200:
                print("SUCCESS! Render worker returned video")
                # Save the video
                with open("debug_output.mp4", "wb") as f:
                    f.write(resp.content)
                print("Saved video to debug_output.mp4")
            else:
                print(f"ERROR: {resp.status_code}")
                print(f"Response body: {resp.text}")
                
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_render_worker())
