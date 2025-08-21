import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load .env file if it exists (for local development)
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
    logger.info("Loaded .env file for local development")
else:
    logger.info("No .env file found, using environment variables")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")
REPLICATE_MODEL_VERSION = os.getenv("REPLICATE_MODEL_VERSION", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")

REPLICATE_POLL_INTERVAL_MS = int(os.getenv("REPLICATE_POLL_INTERVAL_MS", "1500"))
REPLICATE_POLL_TIMEOUT_S = int(os.getenv("REPLICATE_POLL_TIMEOUT_S", "120"))

# Optional: External render worker URL (Option A)
RENDER_WORKER_URL = os.getenv("RENDER_WORKER_URL", "").strip()

VIDEO_WIDTH = int(os.getenv("VIDEO_WIDTH", "1280"))
VIDEO_HEIGHT = int(os.getenv("VIDEO_HEIGHT", "720"))
FPS = int(os.getenv("FPS", "30"))

# Comma-separated list of allowed origins for CORS (e.g., "https://app.vercel.app,https://www.example.com").
# IMPORTANT: Default to wildcard in production unless explicitly set, to avoid blocking the frontend due to CORS.
_allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "").strip()
if _allowed_origins_env:
    ALLOWED_ORIGINS = [o.strip() for o in _allowed_origins_env.split(",") if o.strip()]
else:
    # Fall back to permissive default. For local development, you can set ALLOWED_ORIGINS explicitly.
    ALLOWED_ORIGINS = ["*"]

def has_all_keys() -> bool:
    keys_present = all([OPENAI_API_KEY, REPLICATE_API_TOKEN, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID])
    if not keys_present:
        missing = []
        if not OPENAI_API_KEY: missing.append("OPENAI_API_KEY")
        if not REPLICATE_API_TOKEN: missing.append("REPLICATE_API_TOKEN") 
        if not ELEVENLABS_API_KEY: missing.append("ELEVENLABS_API_KEY")
        if not ELEVENLABS_VOICE_ID: missing.append("ELEVENLABS_VOICE_ID")
        logger.warning(f"Missing API keys: {', '.join(missing)}")
    return keys_present
