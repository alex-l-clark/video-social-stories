import httpx
from .settings import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID

HEADERS = {
    "xi-api-key": ELEVENLABS_API_KEY,
    "Content-Type": "application/json"
}

async def tts_to_bytes(text: str) -> bytes:
    payload = {
        "text": text,  # MVP: plain text; SSML optional depending on voice
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        "optimize_streaming_latency": 2,
        "output_format": "mp3_22050_32"
    }
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, headers=HEADERS, json=payload)
        r.raise_for_status()
        return r.content
