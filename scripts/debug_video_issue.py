#!/usr/bin/env python3
"""
Debug script to test video generation and identify corruption issues.
Run this locally to test the video generation pipeline.
"""

import os
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path

# Add the backend to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "social_story_backend"))

from social_story.social_story.models import StoryRequest
from social_story.social_story.orchestrator import run_pipeline
import asyncio

async def test_video_generation():
    """Test the video generation pipeline locally."""
    
    # Create a test request
    test_request = StoryRequest(
        age=6,
        reading_level="beginner",
        diagnosis_summary="Autism spectrum disorder, responds well to visual stories",
        situation="Learning to share toys with classmates",
        setting="Preschool classroom",
        words_to_avoid=["bad", "wrong", "naughty"],
        voice_preset="calm_child"
    )
    
    print("🚀 Starting video generation test...")
    print(f"Request: {test_request.situation} in {test_request.setting}")
    
    try:
        # Run the pipeline
        final_state = await run_pipeline(test_request)
        
        print(f"✅ Pipeline completed successfully!")
        print(f"Job ID: {final_state.job_id}")
        print(f"Final path: {final_state.final_path}")
        
        if final_state.final_path and os.path.exists(final_state.final_path):
            file_size = os.path.getsize(final_state.final_path)
            print(f"Video file size: {file_size} bytes ({file_size/1024:.1f} KB)")
            
            # Validate MP4 header
            with open(final_state.final_path, "rb") as f:
                header = f.read(12)
                print(f"MP4 header: {header.hex()}")
                
                if header.startswith(b'\x00\x00\x00') or header.startswith(b'ftyp'):
                    print("✅ Valid MP4 header detected")
                else:
                    print("❌ Invalid MP4 header - file may be corrupted")
            
            # Test ffprobe to get video info
            try:
                result = subprocess.run([
                    "ffprobe", "-v", "quiet", "-print_format", "json", 
                    "-show_format", "-show_streams", final_state.final_path
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    print("✅ FFprobe validation passed")
                    # Parse and display basic info
                    import json
                    info = json.loads(result.stdout)
                    format_info = info.get('format', {})
                    print(f"Duration: {format_info.get('duration', 'Unknown')} seconds")
                    print(f"Bitrate: {format_info.get('bit_rate', 'Unknown')} bps")
                else:
                    print(f"❌ FFprobe validation failed: {result.stderr}")
                    
            except Exception as e:
                print(f"⚠️ Could not run ffprobe: {e}")
            
        else:
            print("❌ No final video path found")
            
    except Exception as e:
        print(f"❌ Pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up
        if 'final_state' in locals() and hasattr(final_state, 'tmp_dir'):
            try:
                shutil.rmtree(final_state.tmp_dir, ignore_errors=True)
                print(f"🧹 Cleaned up temporary directory: {final_state.tmp_dir}")
            except Exception as e:
                print(f"⚠️ Failed to clean up: {e}")

def check_ffmpeg():
    """Check if FFmpeg is available."""
    try:
        result = subprocess.run(["ffmpeg", "-version"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✅ FFmpeg available: {version}")
            return True
        else:
            print("❌ FFmpeg not working properly")
            return False
    except Exception as e:
        print(f"❌ FFmpeg not available: {e}")
        return False

def main():
    """Main function."""
    print("🔍 Video Generation Debug Script")
    print("=" * 50)
    
    # Check FFmpeg
    if not check_ffmpeg():
        print("Please install FFmpeg to run this test.")
        return
    
    # Check environment variables
    required_vars = [
        "OPENAI_API_KEY",
        "REPLICATE_API_TOKEN", 
        "ELEVENLABS_API_KEY",
        "ELEVENLABS_VOICE_ID"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these variables before running the test.")
        return
    
    print("✅ All required environment variables are set")
    
    # Run the test
    asyncio.run(test_video_generation())

if __name__ == "__main__":
    main()
