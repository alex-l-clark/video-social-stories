import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")

REPLICATE_POLL_INTERVAL_MS = int(os.getenv("REPLICATE_POLL_INTERVAL_MS", "1500"))
REPLICATE_POLL_TIMEOUT_S = int(os.getenv("REPLICATE_POLL_TIMEOUT_S", "120"))

VIDEO_WIDTH = int(os.getenv("VIDEO_WIDTH", "1280"))
VIDEO_HEIGHT = int(os.getenv("VIDEO_HEIGHT", "720"))
FPS = int(os.getenv("FPS", "30"))

# Comma-separated list of allowed origins for CORS (e.g., "https://app.vercel.app,https://www.example.com")
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]

def has_all_keys() -> bool:
    return all([OPENAI_API_KEY, REPLICATE_API_TOKEN, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID])
