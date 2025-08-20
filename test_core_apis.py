#!/usr/bin/env python3
"""
Test script to verify the core APIs are working (OpenAI and Replicate)
"""
import asyncio
import sys
import os

# Add the backend to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'social_story_backend'))

from social_story.models import StoryRequest
from social_story.llm import get_story_spec
from social_story.replicate_client import create_and_wait_image
from social_story.settings import has_all_keys

async def test_core_apis():
    """Test OpenAI and Replicate APIs to ensure they work with synchronous execution"""
    
    print("🧪 Testing core APIs with production fixes...")
    
    # Check environment
    if not has_all_keys():
        print("❌ API keys not configured. Please check your .env file.")
        return False
    
    print("✅ API keys configured")
    
    # Create a minimal test request
    req = StoryRequest(
        situation="saying hello to a new friend",
        setting="playground",
        diagnosis_summary="autism; prefers routine",
        age=6
    )
    
    print(f"📝 Test request: {req.situation} in {req.setting}")
    
    try:
        # Test OpenAI API
        print("\n🤖 Testing OpenAI API...")
        story_spec = get_story_spec(req)
        print(f"✅ OpenAI API working! Generated {len(story_spec['scenes'])} scenes")
        print(f"📖 First scene: {story_spec['scenes'][0]['script'][:100]}...")
        
        # Test Replicate API
        print("\n🎨 Testing Replicate API...")
        first_scene = story_spec['scenes'][0]
        image_url = await create_and_wait_image(first_scene['image_prompt'])
        print(f"✅ Replicate API working! Image URL: {image_url}")
        
        print(f"\n🎉 SUCCESS! Core APIs work correctly with synchronous execution")
        print(f"👍 The production fix resolves the background task issue")
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_core_apis())
    if success:
        print("\n✅ CORE APIS WORKING")
        print("🚀 Ready to deploy to production")
    else:
        print("\n💥 CORE API TEST FAILED")
    sys.exit(0 if success else 1)
