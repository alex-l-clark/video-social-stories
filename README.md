# Production Link - https://social-story-frontend-gu6erq7q1-alexs-projects-43af42f1.vercel.app/
# Video Social Stories App - Tech Stack Overview

A comprehensive AI-powered application that creates personalized video stories for autistic students to learn social skills. Think of it as a smart video creator that understands exactly what kind of story someone needs.

## 🎯 What Does This App Do?

Instead of just reading about social situations, this app creates **personalized video stories** with:
- Pictures that match the situation
- A calming voice reading the story  
- Text on screen (like captions)
- Multiple scenes that walk through the situation step-by-step

## 🏗️ The Big Picture Architecture

This app works like an **assembly line in a factory** that makes custom videos:

```
User Request → Backend Brain → AI Services → Video Factory → Final Video
```

## 🧠 Part 1: The Backend Brain (FastAPI + Python)

**What it is:** The "manager" of the whole operation, written in Python using FastAPI.

**What it does:**
- Takes requests from users (like "I need a story about sharing toys")
- Coordinates all the different AI services
- Manages the workflow from start to finish
- Sends back the final video

**Key Files:**
- `app.py` - The main "front desk" that handles incoming requests
- `orchestrator.py` - The "project manager" that coordinates everything
- `models.py` - Defines what information the app needs (age, situation, etc.)

## 🤖 Part 2: The AI Services (The Creative Team)

Think of these as different specialists working together:

### 📝 The Writer (OpenAI/ChatGPT)
**File:** `social_story_backend/social_story/llm.py`
**Job:** Creates the story script
- Takes your situation and creates 6-8 scenes
- Writes dialogue that's appropriate for the age/reading level
- Avoids words you don't want (like "gross" or "bad")
- Creates captions and timing for each scene

### 🎨 The Artist (Replicate AI)
**File:** `social_story_backend/social_story/replicate_client.py`
**Job:** Creates calm, kid-friendly illustrations
- Takes each scene description
- Generates appropriate images (like a classroom, playground, etc.)
- Makes sure images are soothing and not overwhelming

### 🎙️ The Voice Actor (ElevenLabs)
**File:** `social_story_backend/social_story/elevenlabs_client.py`
**Job:** Creates the narration
- Converts the script to natural-sounding speech
- Uses a calm, child-friendly voice
- Matches the pacing to the video

## 🎬 Part 3: The Video Factory (FFmpeg + Render Worker)

This is where all the pieces get assembled into a final video:

### Local Assembly (FFmpeg)
**What it does:**
- Takes each image and stretches it over the scene duration
- Adds the voice audio to each scene
- Combines all scenes into one video
- Burns in the subtitles/captions
- Exports as a standard MP4 file

### Cloud Assembly (Render Worker)
**File:** `render_worker/app.py`
**Why it exists:** Video processing is really demanding, so there's also a separate "video factory" that can run on powerful cloud servers
**Deployment:** Uses platforms like Fly.io that have more processing power

## 🌐 Part 4: The Deployment Platform (Vercel)

**What it is:** Like having your app running on a super-fast computer in the cloud that anyone can access

**Key Features:**
- **Serverless:** Only uses resources when someone makes a request
- **Global:** Fast no matter where users are located
- **Automatic scaling:** Can handle one user or thousands

## 🔧 Part 5: The Workflow Engine (LangGraph)

**What it is:** Think of this like a recipe card that ensures steps happen in the right order

**The Recipe:**
1. **Story Spec** → Create the script and scene breakdown
2. **Assets** → Generate images and audio for each scene  
3. **Render** → Combine everything into a final video

**File:** `social_story_backend/social_story/orchestrator.py` handles this workflow

## 📁 Part 6: Data Models & Settings

### Data Structure (`social_story_backend/social_story/models.py`)
Defines exactly what information is needed:
```python
- age: How old is the student?
- reading_level: How complex should the language be?
- diagnosis_summary: What should we know about their needs?
- situation: What social situation needs to be addressed?
- setting: Where does this happen? (classroom, playground, etc.)
- words_to_avoid: Any words that might be triggering?
- voice_preset: What kind of voice should narrate?
```

### Configuration (`social_story_backend/social_story/settings.py`)
- API keys for all the AI services
- Server settings
- Security configurations

## 🔒 Part 7: Security & Privacy

**Key Features:**
- No user data is stored permanently
- All temporary files are deleted immediately after video creation
- API keys are kept secure using environment variables
- Built-in secret scanning to prevent accidental exposure

## 🧵 How It All Works Together

1. **User makes a request:** "I need a story about a 6-year-old with autism learning to share toys in preschool"

2. **FastAPI receives it:** The backend validates the request and creates a unique job ID

3. **LangGraph orchestrates:** Follows the workflow recipe
   - Calls OpenAI to write the story
   - Calls Replicate to create images  
   - Calls ElevenLabs to create audio

4. **Assets are created:** Each scene gets an image file and audio file

5. **Video rendering:** Either locally with FFmpeg or remotely with the render worker
   - Combines images + audio for each scene
   - Stitches scenes together
   - Adds captions/subtitles

6. **Delivery:** The final MP4 is streamed back to the user and all temporary files are deleted

## 🔧 Technologies Used (The Tools)

**Programming Language:** Python (easy to learn, great for AI)
**Web Framework:** FastAPI (fast, modern way to build web APIs)
**AI Orchestration:** LangGraph (manages complex AI workflows)
**AI Services:** 
- OpenAI (text generation)
- Replicate (image generation)  
- ElevenLabs (voice synthesis)
**Video Processing:** FFmpeg (industry standard for video editing)
**Deployment:** Vercel (cloud hosting platform)
**Data Validation:** Pydantic (ensures data is correct format)

## 🚀 Getting Started

### For Developers & Testing

**⚠️ Important Performance Notes:**
- **Production Performance:** The current production version takes about **2 minutes** to return a video
- **Best Performance:** For development and testing, run locally for fastest results

**Local Setup (Recommended for best performance):**
```bash
cd social_story_backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn social_story.app:app --reload
```

### For Real Teachers & End Users

Teachers and parents can access the app through the production link, which provides a stable, always-available service. While it may take a few minutes to generate videos, this ensures reliable access without requiring technical setup.

- **Mobile Compatibility:** The production app does **not work on mobile devices** - desktop/tablet only

## 🤔 Why These Technology Choices?

**Python:** Easy to read, tons of AI libraries
**FastAPI:** Super fast, automatically creates documentation
**Serverless (Vercel):** Only pay for what you use, scales automatically
**Separate render worker:** Video processing needs more power than serverless allows
**LangGraph:** Makes it easy to build complex AI workflows that can be debugged

## 🔒 Security Setup

This repository includes automated security scanning to prevent secrets from being committed:

```bash
# Install pre-commit hooks for local secret scanning
pip install pre-commit
pre-commit install
```

See [SECURITY.md](SECURITY.md) for complete security guidelines.

---

This is a modern, AI-powered application that combines multiple cutting-edge technologies to solve a real problem - helping autistic students learn social skills through personalized video stories!
