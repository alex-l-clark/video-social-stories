# Social Story Backend (MVP)

FastAPI + LangGraph backend to generate social story videos:
- LLM (OpenAI) creates a Story Spec JSON (6–8 scenes, SRT).
- Replicate generates a calm illustration per scene (polled, no webhooks).
- ElevenLabs synthesizes per-scene voice.
- FFmpeg stitches to a 720p MP4 with gentle Ken Burns and burned-in captions.
- The server streams the MP4 to the client and **deletes all temp files immediately afterward**.

## Quickstart

1) **Install FFmpeg** (required):
   ```bash
   ffmpeg -version
   ```

2) **Create env**:
   ```bash
   cp .env.example .env
   # fill in OPENAI_API_KEY, REPLICATE_API_TOKEN, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID
   ```

3) **Install Python deps**:
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

4) **Run**:
   ```bash
   uvicorn social_story.app:app --reload
   ```

5) **Test**:
   ```bash
   curl -X POST http://localhost:8000/v1/social-story:render          -H "Content-Type: application/json"          -d '{
       "age":6,
       "reading_level":"early_reader",
       "diagnosis_summary":"autism; sound sensitivity; prefers routine",
       "situation":"passing gas in class and laughing to get attention",
       "setting":"elementary classroom",
       "words_to_avoid":["gross","bad"],
       "voice_preset":"calm_childlike_female"
     }'          -o story.mp4
   ```

## Notes

- English + first-person is assumed.
- No login; no persistence of PII or files on server after download.
- To change image model, set `MODEL` in `social_story/replicate_client.py` to a specific version ID you trust.
- For stricter redaction, enhance `_redact()` in `social_story/llm.py`.
