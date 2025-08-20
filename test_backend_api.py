#!/usr/bin/env python3
"""
Test the backend API to verify it works for production
"""
import asyncio
import httpx
import json
import sys
import os

# Add the backend module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'social_story_backend'))

from social_story.settings import has_all_keys

async def test_backend_api():
    """Test the backend API by making a real request"""
    
    # Check if we have API keys
    if not has_all_keys():
        print("Missing API keys. Please check your .env file.")
        return
    
    # Test request data
    request_data = {
        "age": 6,
        "reading_level": "early_reader",
        "diagnosis_summary": "autism; prefers routine",
        "situation": "A child is nervous about their first day of school",
        "setting": "Elementary school classroom",
        "words_to_avoid": [],
        "voice_preset": "calm_childlike_female"
    }
    
    print("Testing backend API locally...")
    print(f"Request: {request_data}")
    
    try:
        # Start the server in the background
        import subprocess
        import time
        import signal
        
        # Start uvicorn server
        server_process = subprocess.Popen([
            "python", "-m", "uvicorn", 
            "social_story.app:app", 
            "--host", "127.0.0.1", 
            "--port", "8001"
        ], cwd="social_story_backend")
        
        # Wait for server to start
        time.sleep(3)
        
        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                "http://127.0.0.1:8001/v1/social-story:render",
                json=request_data
            )
            
            print(f"Response status: {response.status_code}")
            if response.status_code == 200:
                # Get the video content
                video_content = response.content
                print(f"Success! Generated video with {len(video_content)} bytes")
                
                # Save the video
                output_path = "test_api_output.mp4"
                with open(output_path, "wb") as f:
                    f.write(video_content)
                print(f"Saved video to {output_path}")
                
                return True
            else:
                print(f"Error response: {response.text}")
                return False
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up server
        try:
            server_process.terminate()
            server_process.wait(timeout=5)
        except:
            try:
                server_process.kill()
            except:
                pass

if __name__ == "__main__":
    success = asyncio.run(test_backend_api())
    if success:
        print("✅ Backend API test successful!")
    else:
        print("❌ Backend API test failed!")
        sys.exit(1)
