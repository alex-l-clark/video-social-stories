#!/usr/bin/env python3
"""
Test the full local backend to see if it uses render worker or local ffmpeg
"""
import asyncio
import sys
import os
import httpx

# Add the backend to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'social_story_backend'))

from social_story.models import StoryRequest
from social_story.orchestrator import run_pipeline

async def test_full_backend():
    """Test the full backend locally"""
    
    print("Testing full backend locally...")
    
    # Create a simple request
    req = StoryRequest(
        situation="A child is nervous about their first day of school",
        setting="Elementary school classroom", 
        tone="encouraging",
        age_group="5-8"
    )
    
    print(f"Request: {req}")
    
    try:
        # Test the full pipeline
        print("\nRunning full pipeline...")
        final_state = await run_pipeline(req)
        
        # Check results
        final_path = final_state.get("final_path") if hasattr(final_state, 'get') else final_state.final_path
        tmp_dir = final_state.get("tmp_dir") if hasattr(final_state, 'get') else final_state.tmp_dir
        
        print(f"Final path: {final_path}")
        print(f"File exists: {os.path.exists(final_path) if final_path else False}")
        if final_path and os.path.exists(final_path):
            print(f"File size: {os.path.getsize(final_path)} bytes")
        
        print("SUCCESS! Full pipeline worked locally")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_backend())
