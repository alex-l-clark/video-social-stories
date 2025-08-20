Render Worker (Option A)

Simple FastAPI service that accepts scene image/audio files and an SRT file, renders per-scene videos with ffmpeg, concatenates them, burns subtitles, and returns the final MP4.

Endpoints:
- POST /render: multipart form-data with files and minimal scene metadata

Deploy targets: Fly.io, Render, or any VM with Docker.


