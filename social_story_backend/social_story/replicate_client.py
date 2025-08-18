import os, time, httpx, asyncio, logging
from .settings import REPLICATE_POLL_INTERVAL_MS, REPLICATE_POLL_TIMEOUT_S, REPLICATE_MODEL_VERSION

logger = logging.getLogger(__name__)

def _headers():
    token = os.getenv("REPLICATE_API_TOKEN", "")
    if not token:
        raise RuntimeError("REPLICATE_API_TOKEN is not set; please configure your .env")
    return {"Authorization": f"Token {token}"}

def _model_selector() -> str:
    # Prefer explicit version from env for stability; fall back to a public model alias (latest).
    return REPLICATE_MODEL_VERSION or "black-forest-labs/flux-schnell"

def _parse_selector(selector: str):
    # Returns a tuple (mode, data)
    # mode == "version": data={"version": <hash>}
    # mode == "model": data={"owner": <owner>, "name": <name>}
    if "/" in selector:
        # Could be owner/name or owner/name:versionAlias
        owner_name, _, _version_alias = selector.partition(":")
        if "/" in owner_name:
            owner, name = owner_name.split("/", 1)
            return "model", {"owner": owner, "name": name}
    # Fallback assume it's a version hash
    return "version", {"version": selector}

async def _asleep(sec: float):
    await asyncio.sleep(sec)

async def create_and_wait_image(prompt: str) -> str:
    logger.info(f"Starting Replicate image generation for prompt: {prompt[:100]}...")
    
    async with httpx.AsyncClient(timeout=30) as client:
        selector = _model_selector()
        logger.info(f"Using Replicate model: {selector}")
        
        json_body = {
            "input": {
                "prompt": f"{prompt}, flat, classroom-friendly illustration, simple shapes, soft colors, clean background, no text on walls",
                "num_outputs": 1
            }
        }
        mode, data = _parse_selector(selector)
        if mode == "version":
            json_body["version"] = data["version"]
            url = "https://api.replicate.com/v1/predictions"
        else:
            url = f"https://api.replicate.com/v1/models/{data['owner']}/{data['name']}/predictions"

        logger.info(f"Sending request to Replicate: {url}")
        r = await client.post(
            url,
            headers={**_headers(), "Content-Type": "application/json"},
            json=json_body,
        )
        if r.status_code >= 400:
            # Surface useful error context
            logger.error(f"Replicate create failed {r.status_code}: {r.text}")
            raise RuntimeError(f"Replicate create failed {r.status_code}: {r.text}")
        pred = r.json()
        pred_id = pred["id"]
        logger.info(f"Replicate prediction created with ID: {pred_id}")

        start = time.time()
        while True:
            s = await client.get(
                f"https://api.replicate.com/v1/predictions/{pred_id}",
                headers=_headers()
            )
            if s.status_code >= 400:
                logger.error(f"Replicate status failed {s.status_code}: {s.text}")
                raise RuntimeError(f"Replicate status failed {s.status_code}: {s.text}")
            body = s.json()
            status = body.get("status")
            logger.info(f"Replicate prediction {pred_id} status: {status}")
            
            if status in ("succeeded", "failed", "canceled"):
                if status != "succeeded":
                    logs = body.get("logs")
                    error_detail = body.get("error")
                    logger.error(f"Replicate failed: {status}. logs={logs} error={error_detail}")
                    raise RuntimeError(f"Replicate failed: {status}. logs={logs} error={error_detail}")
                output = body.get("output")
                if isinstance(output, list) and output:
                    logger.info(f"Replicate prediction succeeded, got output URL: {output[0]}")
                    return output[0]
                logger.error("Replicate succeeded but no output URL")
                raise RuntimeError("Replicate succeeded but no output URL")
            if time.time() - start > REPLICATE_POLL_TIMEOUT_S:
                logger.error("Replicate polling timeout")
                raise TimeoutError("Replicate polling timeout")
            await _asleep(REPLICATE_POLL_INTERVAL_MS / 1000.0)
