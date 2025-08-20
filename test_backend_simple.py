#!/usr/bin/env python3
"""
Simple test script to test the backend's story generation
"""
import asyncio
import sys
import os

# Add the backend to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'social_story_backend'))

from social_story.models import StoryRequest
from social_story.llm import get_story_spec
from social_story.replicate_client import create_and_wait_image
from social_story.elevenlabs_client import tts_to_bytes

async def test_story_generation():
    """Test just the story generation part"""
    
    print("Testing story generation...")
    
    # Create a simple request
    req = StoryRequest(
        situation="A child is nervous about their first day of school",
        setting="Elementary school classroom", 
        tone="encouraging",
        age_group="5-8"
    )
    
    print(f"Request: {req}")
    
    try:
        # Test story spec generation
        print("\n1. Generating story spec...")
        raw_spec = get_story_spec(req)
        print(f"Raw spec: {raw_spec}")
        
        # Test image generation for first scene
        print("\n2. Testing image generation...")
        first_scene = raw_spec['scenes'][0]
        print(f"First scene image prompt: {first_scene['image_prompt']}")
        
        image_url = await create_and_wait_image(first_scene['image_prompt'])
        print(f"Image URL: {image_url}")
        
        # Test audio generation for first scene
        print("\n3. Testing audio generation...")
        first_scene_script = first_scene['script']
        print(f"First scene script: {first_scene_script}")
        
        audio_bytes = await tts_to_bytes(first_scene_script)
        print(f"Audio generated: {len(audio_bytes)} bytes")
        
        print("\nSUCCESS! All components working")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_story_generation())
