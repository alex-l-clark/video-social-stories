# Social Stories (Full-stack)

Monorepo with:
- `social_story_frontend` (Vite + React + shadcn-ui)
- `social_story_backend` (FastAPI + LangGraph + OpenAI + Replicate + ElevenLabs)

## Local Development

### Backend
1. Install FFmpeg and Python deps:
   ```bash
   cd social_story_backend
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Configure env:
   ```bash
   cp env.example .env
   # Fill in: OPENAI_API_KEY, REPLICATE_API_TOKEN, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID
   # Optionally set ALLOWED_ORIGINS=http://localhost:5173
   ```
3. Run the API:
   ```bash
   uvicorn social_story.app:app --reload
   # API at http://localhost:8000
   ```

### Frontend
1. Install Node deps:
   ```bash
   cd social_story_frontend
   npm i
   ```
2. Configure env (optional for local, defaults to localhost backend):
   ```bash
   cp env.example .env
   # VITE_API_BASE_URL=http://localhost:8000
   ```
3. Start dev server:
   ```bash
   npm run dev
   # App at http://localhost:5173
   ```

## Deployment (Vercel + any backend host)

- Frontend (Vercel):
  - Set Environment Variable: `VITE_API_BASE_URL` to your backend URL (e.g., `https://api.yourdomain.com`).
  - Build command: `npm run build` (auto-detected), Output: `dist/`.

- Backend (example: Railway/Render/Fly):
  - Set env vars: `OPENAI_API_KEY`, `REPLICATE_API_TOKEN`, `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`.
  - Set `ALLOWED_ORIGINS` to your Vercel URL(s), e.g., `https://your-app.vercel.app`.
  - Start command: `uvicorn social_story.app:app --host 0.0.0.0 --port 8000`.

Once deployed, update Vercel `VITE_API_BASE_URL` to the backend’s HTTPS URL.
