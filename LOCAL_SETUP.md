# Local Development Setup

This guide helps you run both the frontend and backend together for the full Social Story experience locally.

## 🚀 Quick Start

### 1. Start the Backend Server

```bash
cd social_story_backend
source .venv/bin/activate
uvicorn social_story.app:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at: **http://localhost:8000**

### 2. Patch and Start the Frontend Server

```bash
# Make sure you're in the project root directory (video-social-stories)
# NOT in the social_story_backend folder

# First, patch the frontend to use local API URLs
python3 patch_frontend.py

# Then start the debug proxy server
python3 debug_api.py
```

The frontend will be available at: **http://localhost:3002**  
(The proxy server serves the patched frontend and forwards API calls to the backend)

**Important:** Make sure you run these commands from the main project directory, not from inside the `social_story_backend` folder!

### 3. Test the Integration

Run the automated integration test:

```bash
python3 test_integration.py
```

## 🌐 Access Your Application

- **Frontend (Web Interface):** http://localhost:3002
- **Backend API:** http://localhost:8000
- **Health Check:** http://localhost:8000/health

## 🔧 Configuration

### Backend Configuration
- All API keys are properly configured (OpenAI, Replicate, ElevenLabs)
- CORS is configured to allow requests from `localhost:3000`
- Environment variables loaded from `.env` file

### Frontend Configuration
- Built React application served as static files
- Configured to make API calls to the backend
- Responsive design for creating social stories

## 🧪 Testing

The integration test (`test_integration.py`) verifies:
- ✅ Frontend accessibility
- ✅ Backend health and API key configuration
- ✅ Complete story generation workflow
- ✅ Job creation, monitoring, and completion

## 📝 API Endpoints

### Async Workflow (Recommended)
- `POST /v1/social-story:start` - Start story generation job
- `GET /v1/jobs/{job_id}` - Check job status  
- `GET /v1/jobs/{job_id}/download` - Download completed video

### Direct Workflow (Legacy)
- `POST /v1/social-story:render` - Generate and stream video directly

## 🎬 Story Generation Process

1. **Input:** User provides story details via web interface
2. **LLM:** OpenAI generates story script and scene descriptions
3. **Images:** Replicate creates calm illustrations for each scene
4. **Audio:** ElevenLabs synthesizes voiceover
5. **Video:** FFmpeg combines everything into MP4 with captions
6. **Download:** User receives the completed social story video

## 🔍 Troubleshooting

If you encounter issues:

1. **Backend not starting:** Check API keys in `.env` file
2. **Frontend not loading:** Ensure port 3000 is available
3. **CORS errors:** Verify backend CORS settings include localhost:3000
4. **Job failures:** Check backend logs in `uvicorn.log`

## 🚦 Server Status

Both servers should show:
- Backend: Green status at http://localhost:8000/health
- Frontend: Social Story Creator page loads at http://localhost:3002

Your Social Story application is now ready for local development and testing!
