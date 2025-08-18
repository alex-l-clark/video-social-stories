#!/usr/bin/env python3
"""
Production diagnosis script for social story backend.
This script tests API connectivity and configuration without running the full pipeline.
"""

import os
import asyncio
import logging
from pathlib import Path

# Add the social_story package to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from social_story.settings import has_all_keys, OPENAI_API_KEY, REPLICATE_API_TOKEN, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_openai():
    """Test OpenAI API connectivity"""
    logger.info("Testing OpenAI API...")
    try:
        from social_story.llm import _get_client
        client = _get_client()
        
        # Simple test call
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'test' and nothing else."}],
            max_tokens=10
        )
        content = resp.choices[0].message.content
        logger.info(f"OpenAI test successful. Response: {content}")
        return True
    except Exception as e:
        logger.error(f"OpenAI test failed: {str(e)}")
        return False

async def test_replicate():
    """Test Replicate API connectivity"""
    logger.info("Testing Replicate API...")
    try:
        from social_story.replicate_client import _headers
        import httpx
        
        # Test auth by listing models
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                "https://api.replicate.com/v1/models",
                headers=_headers()
            )
            resp.raise_for_status()
            models = resp.json()
            logger.info(f"Replicate test successful. Found {len(models.get('results', []))} models")
            return True
    except Exception as e:
        logger.error(f"Replicate test failed: {str(e)}")
        return False

async def test_elevenlabs():
    """Test ElevenLabs API connectivity"""
    logger.info("Testing ElevenLabs API...")
    try:
        from social_story.elevenlabs_client import _headers, _voice_id
        import httpx
        
        # Test auth by getting voice info
        voice_id = _voice_id()
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"https://api.elevenlabs.io/v1/voices/{voice_id}",
                headers=_headers()
            )
            resp.raise_for_status()
            voice_info = resp.json()
            logger.info(f"ElevenLabs test successful. Voice: {voice_info.get('name', 'Unknown')}")
            return True
    except Exception as e:
        logger.error(f"ElevenLabs test failed: {str(e)}")
        return False

def check_environment():
    """Check environment configuration"""
    logger.info("Checking environment configuration...")
    
    logger.info(f"OPENAI_API_KEY present: {'Yes' if OPENAI_API_KEY else 'No'}")
    logger.info(f"REPLICATE_API_TOKEN present: {'Yes' if REPLICATE_API_TOKEN else 'No'}")  
    logger.info(f"ELEVENLABS_API_KEY present: {'Yes' if ELEVENLABS_API_KEY else 'No'}")
    logger.info(f"ELEVENLABS_VOICE_ID present: {'Yes' if ELEVENLABS_VOICE_ID else 'No'}")
    
    all_keys = has_all_keys()
    logger.info(f"All required keys present: {'Yes' if all_keys else 'No'}")
    
    return all_keys

async def run_diagnostics():
    """Run all diagnostic tests"""
    logger.info("Starting production diagnostics...")
    
    # Check environment
    env_ok = check_environment()
    if not env_ok:
        logger.error("Environment check failed. Please ensure all API keys are set.")
        return False
    
    # Test APIs
    openai_ok = await test_openai()
    replicate_ok = await test_replicate() 
    elevenlabs_ok = await test_elevenlabs()
    
    all_ok = openai_ok and replicate_ok and elevenlabs_ok
    
    logger.info(f"Diagnostics complete. All tests passed: {'Yes' if all_ok else 'No'}")
    
    if not all_ok:
        logger.error("Some API tests failed. Check the logs above for details.")
    
    return all_ok

if __name__ == "__main__":
    success = asyncio.run(run_diagnostics())
    sys.exit(0 if success else 1)
