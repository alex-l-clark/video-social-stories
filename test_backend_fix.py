#!/usr/bin/env python3
"""
Test script to verify the backend fix is working.
"""

import asyncio
import httpx
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_health_endpoint(base_url: str = "http://localhost:8000"):
    """Test the /health endpoint"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{base_url}/health")
            resp.raise_for_status()
            health = resp.json()
            logger.info(f"Health check response: {health}")
            return health.get("has_keys", False)
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return False

async def test_job_creation(base_url: str = "http://localhost:8000"):
    """Test creating a job"""
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "situation": "going to the dentist",
                "setting": "dental office",
                "age": 6,
                "reading_level": "early_reader",
                "diagnosis_summary": "autism; prefers routine"
            }
            
            resp = await client.post(
                f"{base_url}/v1/social-story:start", 
                json=payload,
                timeout=10
            )
            resp.raise_for_status()
            result = resp.json()
            logger.info(f"Job creation response: {result}")
            return result.get("job_id")
    except Exception as e:
        logger.error(f"Job creation failed: {str(e)}")
        return None

async def test_job_status(base_url: str, job_id: str):
    """Test checking job status"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{base_url}/v1/jobs/{job_id}")
            resp.raise_for_status()
            status = resp.json()
            logger.info(f"Job status response: {status}")
            return status
    except Exception as e:
        logger.error(f"Job status check failed: {str(e)}")
        return None

async def run_tests():
    """Run all tests"""
    logger.info("Starting backend tests...")
    
    # Test health
    health_ok = await test_health_endpoint()
    if not health_ok:
        logger.error("Health check indicates missing API keys")
        return False
    
    # Test job creation
    job_id = await test_job_creation()
    if not job_id:
        logger.error("Job creation failed")
        return False
    
    # Wait a bit and check status
    await asyncio.sleep(2)
    status = await test_job_status("http://localhost:8000", job_id)
    if not status:
        logger.error("Job status check failed")
        return False
    
    # Check if job is progressing
    if status.get("status") in ["running", "succeeded"]:
        logger.info("Job is progressing normally!")
        return True
    elif status.get("status") == "failed":
        logger.error(f"Job failed: {status.get('error')}")
        return False
    else:
        logger.info(f"Job status: {status.get('status')}")
        return True

if __name__ == "__main__":
    success = asyncio.run(run_tests())
    if success:
        logger.info("All tests passed!")
    else:
        logger.error("Some tests failed!")
