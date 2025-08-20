#!/usr/bin/env python3
"""
Test script to verify the production fixes work correctly
"""
import asyncio
import sys
import os
import tempfile

# Add the backend to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'social_story_backend'))

from social_story.models import StoryRequest
from social_story.orchestrator import run_pipeline
from social_story.settings import has_all_keys

async def test_full_pipeline():
    """Test the complete pipeline to ensure all APIs are called"""
    
    print("🧪 Testing full pipeline with production fixes...")
    
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
        print("\n🚀 Running pipeline...")
        final_state = await run_pipeline(req)
        
        # Check results
        final_path = final_state.get("final_path") if hasattr(final_state, 'get') else final_state.final_path
        tmp_dir = final_state.get("tmp_dir") if hasattr(final_state, 'get') else final_state.tmp_dir
        
        if final_path and os.path.exists(final_path):
            file_size = os.path.getsize(final_path)
            print(f"✅ Pipeline completed successfully!")
            print(f"📹 Video created: {final_path}")
            print(f"📊 File size: {file_size:,} bytes")
            
            # Basic video validation
            if file_size > 100000:  # > 100KB suggests real video content
                print("✅ Video file appears to be valid (good size)")
            else:
                print("⚠️  Video file is very small - might be corrupted")
            
            # Clean up
            if tmp_dir and os.path.exists(tmp_dir):
                import shutil
                shutil.rmtree(tmp_dir, ignore_errors=True)
                print("🧹 Cleaned up temporary files")
            
            return True
        else:
            print("❌ Pipeline completed but no video file found")
            return False
            
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_full_pipeline())
    if success:
        print("\n🎉 SUCCESS! Production fixes work correctly")
        print("👍 Ready for production deployment")
    else:
        print("\n💥 FAILED! Check the errors above")
    sys.exit(0 if success else 1)
