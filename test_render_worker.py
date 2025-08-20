#!/usr/bin/env python3
"""
Test the render worker directly with real content
"""
import asyncio
import httpx
import tempfile
import os
import sys

# Add the backend module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'social_story_backend'))

from social_story.elevenlabs_client import tts_to_bytes
from social_story.replicate_client import create_and_wait_image
from social_story.settings import has_all_keys

async def test_render_worker():
    """Test the render worker with real audio and image files"""
    
    # Check if we have API keys
    if not has_all_keys():
        print("Missing API keys. Please check your .env file.")
        return
    
    # Create test files
    tmp_dir = tempfile.mkdtemp()
    print(f"Created temp dir: {tmp_dir}")
    
    try:
        # Generate a real image
        print("Generating test image...")
        image_url = await create_and_wait_image("A simple red circle on white background")
        
        # Download and save the image as PNG
        async with httpx.AsyncClient() as client:
            resp = await client.get(image_url)
            if image_url.endswith('.webp'):
                # Convert WebP to PNG
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(resp.content))
                img_path = os.path.join(tmp_dir, "scene_1.png")
                img.save(img_path, 'PNG')
            else:
                img_path = os.path.join(tmp_dir, "scene_1.png")
                with open(img_path, "wb") as f:
                    f.write(resp.content)
        
        # Generate real audio
        print("Generating test audio...")
        audio_bytes = await tts_to_bytes("Hello world, this is a test.")
        
        # Save the audio
        audio_path = os.path.join(tmp_dir, "scene_1.mp3")
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)
        
        print(f"Audio file size: {len(audio_bytes)} bytes")
        
        # Create SRT file
        srt_path = os.path.join(tmp_dir, "story.srt")
        with open(srt_path, "w") as f:
            f.write("1\n00:00:00,000 --> 00:00:05,000\nHello world, this is a test.\n")
        
        # Test the render worker
        files = [
            ("files", ("scene_1.png", open(img_path, "rb"), "image/png")),
            ("files", ("scene_1.mp3", open(audio_path, "rb"), "audio/mpeg")),
            ("subs", ("story.srt", open(srt_path, "rb"), "application/x-subrip"))
        ]
        
        scenes_data = [{"id": 1, "duration_sec": 5}]
        form_data = {"scenes": str(scenes_data)}
        
        print("Sending request to render worker...")
        
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post("https://social-story-renderer.fly.dev/render", files=files, data=form_data)
            print(f"Response status: {resp.status_code}")
            print(f"Response headers: {dict(resp.headers)}")
            
            if resp.status_code >= 400:
                print(f"Error response: {resp.text}")
            else:
                print(f"Success! Got {len(resp.content)} bytes")
                # Save the output video
                output_path = os.path.join(os.path.dirname(__file__), "test_output.mp4")
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                print(f"Saved video to {output_path}")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close files
        try:
            for _, (_, fh, _) in files:
                fh.close()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_render_worker())
