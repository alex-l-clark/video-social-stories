import time, httpx, asyncio
from .settings import REPLICATE_API_TOKEN, REPLICATE_POLL_INTERVAL_MS, REPLICATE_POLL_TIMEOUT_S

HEADERS = {"Authorization": f"Token {REPLICATE_API_TOKEN}"}

# Replace with a concrete version slug if needed for stability.
MODEL = "stability-ai/sdxl"

async def _asleep(sec: float):
    await asyncio.sleep(sec)

async def create_and_wait_image(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            "https://api.replicate.com/v1/predictions",
            headers={**HEADERS, "Content-Type": "application/json"},
            json={
                "version": MODEL,
                "input": {
                    "prompt": f"{prompt}, flat, classroom-friendly illustration, simple shapes, soft colors, clean background, no text on walls",
                    "num_outputs": 1
                }
            }
        )
        r.raise_for_status()
        pred = r.json()
        pred_id = pred["id"]

        start = time.time()
        while True:
            s = await client.get(
                f"https://api.replicate.com/v1/predictions/{pred_id}",
                headers=HEADERS
            )
            s.raise_for_status()
            body = s.json()
            status = body.get("status")
            if status in ("succeeded", "failed", "canceled"):
                if status != "succeeded":
                    raise RuntimeError(f"Replicate failed: {status}")
                output = body.get("output")
                if isinstance(output, list) and output:
                    return output[0]
                raise RuntimeError("Replicate succeeded but no output URL")
            if time.time() - start > REPLICATE_POLL_TIMEOUT_S:
                raise TimeoutError("Replicate polling timeout")
            await _asleep(REPLICATE_POLL_INTERVAL_MS / 1000.0)
