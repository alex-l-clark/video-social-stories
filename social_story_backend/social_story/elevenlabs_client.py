import os, httpx, asyncio
import time

def _voice_id() -> str:
    vid = os.getenv("ELEVENLABS_VOICE_ID", "")
    if not vid:
        raise RuntimeError("ELEVENLABS_VOICE_ID is not set; please configure your .env")
    return vid

def _headers():
    api_key = os.getenv("ELEVENLABS_API_KEY", "")
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY is not set; please configure your .env")
    return {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }

async def tts_to_bytes(text: str, max_retries: int = 3) -> bytes:
    payload = {
        "text": text,  # MVP: plain text; SSML optional depending on voice
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        "optimize_streaming_latency": 2,
        "output_format": "mp3_22050_32"
    }
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{_voice_id()}"
    
    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.post(url, headers=_headers(), json=payload)
                r.raise_for_status()
                return r.content
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:  # Rate limited
                if attempt < max_retries:
                    # Exponential backoff: wait 2^attempt seconds
                    wait_time = 2 ** attempt
                    print(f"ElevenLabs rate limited (429). Retrying in {wait_time} seconds... (attempt {attempt + 1}/{max_retries + 1})")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    print(f"ElevenLabs rate limit exceeded after {max_retries + 1} attempts. Please wait before trying again.")
                    raise
            else:
                # Other HTTP errors, don't retry
                raise
        except Exception as e:
            # Other errors (network, timeout, etc), don't retry
            raise
