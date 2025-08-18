"""
Vercel KV integration for job state management.
This allows jobs to persist across serverless function invocations.
"""
import os
import json
import httpx
import logging
from typing import Dict, Any, Optional
from .models import OrchestrationState, StoryRequest

logger = logging.getLogger(__name__)

class KVStorage:
    def __init__(self):
        self.kv_rest_api_url = os.getenv("KV_REST_API_URL")
        self.kv_rest_api_token = os.getenv("KV_REST_API_TOKEN")
        
        if not self.kv_rest_api_url or not self.kv_rest_api_token:
            logger.warning("KV storage not configured - falling back to in-memory storage")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("KV storage enabled")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.kv_rest_api_token}",
            "Content-Type": "application/json"
        }

    async def set_job(self, job_id: str, job_data: Dict[str, Any]) -> bool:
        """Store job data in KV"""
        if not self.enabled:
            return False
            
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{self.kv_rest_api_url}/set",
                    headers=self._headers(),
                    json=[f"job:{job_id}", json.dumps(job_data)]
                )
                response.raise_for_status()
                logger.info(f"Stored job {job_id} in KV")
                return True
        except Exception as e:
            logger.error(f"Failed to store job {job_id} in KV: {e}")
            return False

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve job data from KV"""
        if not self.enabled:
            return None
            
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{self.kv_rest_api_url}/get",
                    headers=self._headers(),
                    json=[f"job:{job_id}"]
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("result"):
                    job_data = json.loads(data["result"])
                    logger.info(f"Retrieved job {job_id} from KV")
                    return job_data
                else:
                    logger.info(f"Job {job_id} not found in KV")
                    return None
        except Exception as e:
            logger.error(f"Failed to retrieve job {job_id} from KV: {e}")
            return None

    async def update_job_status(self, job_id: str, status: str, error: str = None, **kwargs) -> bool:
        """Update job status in KV"""
        job_data = await self.get_job(job_id)
        if not job_data:
            logger.error(f"Cannot update job {job_id} - not found in KV")
            return False
            
        job_data["status"] = status
        if error:
            job_data["error"] = error
        
        # Update any additional fields
        for key, value in kwargs.items():
            job_data[key] = value
            
        return await self.set_job(job_id, job_data)

    async def set_scene_asset(self, job_id: str, scene_id: int, asset_type: str, url: str) -> bool:
        """Store scene asset URL in KV"""
        key = f"asset:{job_id}:{scene_id}:{asset_type}"
        
        if not self.enabled:
            return False
            
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{self.kv_rest_api_url}/set",
                    headers=self._headers(),
                    json=[key, url]
                )
                response.raise_for_status()
                logger.info(f"Stored asset {key} in KV")
                return True
        except Exception as e:
            logger.error(f"Failed to store asset {key} in KV: {e}")
            return False

    async def get_scene_asset(self, job_id: str, scene_id: int, asset_type: str) -> Optional[str]:
        """Retrieve scene asset URL from KV"""
        key = f"asset:{job_id}:{scene_id}:{asset_type}"
        
        if not self.enabled:
            return None
            
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{self.kv_rest_api_url}/get",
                    headers=self._headers(),
                    json=[key]
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("result"):
                    logger.info(f"Retrieved asset {key} from KV")
                    return data["result"]
                else:
                    return None
        except Exception as e:
            logger.error(f"Failed to retrieve asset {key} from KV: {e}")
            return None

# Global KV instance
kv = KVStorage()
