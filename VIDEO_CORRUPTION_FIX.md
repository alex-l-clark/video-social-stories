# Video Corruption Issue - Analysis and Fix

## Problem Description

The production deployment was returning corrupted MP4 files that were only 26 bytes in size, compared to the expected 1000-1500 KB for completed videos. This issue appeared after recent file cleanup and deployment changes.

## Root Cause Analysis

The corruption was caused by **asynchronous streaming response handling issues** in the render worker, specifically:

1. **Premature cleanup**: Temporary files were being cleaned up while still streaming
2. **File handle management**: File handles were being closed before streaming completed
3. **Serverless context termination**: In serverless environments, background tasks can be killed when the function execution context ends
4. **Streaming interruption**: The streaming response was being interrupted before completion

## Technical Details

### The Problem in `render_worker/app.py`

The original code had this problematic pattern:

```python
def iterfile():
    try:
        with open(final_path, "rb") as f:
            # ... streaming logic ...
    finally:
        # This cleanup happened too early!
        shutil.rmtree(tmp, ignore_errors=True)
```

The issue was that the cleanup in the `finally` block could execute before the streaming was complete, especially in serverless environments where the execution context might end abruptly.

### Why 26 Bytes?

A 26-byte MP4 file typically indicates:
- Only the file header was written
- The stream was interrupted immediately after starting
- File handles were closed prematurely

## Applied Fixes

### 1. Fixed Render Worker (`render_worker/app.py`)

- **Memory-based streaming**: Instead of streaming from file handles, read the entire video into memory first
- **Early cleanup**: Clean up temporary files before starting the stream
- **Better validation**: Added file size and MP4 header validation
- **Improved error handling**: Better error messages and cleanup on failure

```python
# Read entire file into memory before streaming
with open(final_path, "rb") as f:
    video_data = f.read()

# Clean up before streaming
shutil.rmtree(tmp, ignore_errors=True)

# Stream from memory
def iterfile():
    chunk_size = 64 * 1024
    for i in range(0, len(video_data), chunk_size):
        yield video_data[i:i + chunk_size]
```

### 2. Enhanced Orchestrator (`social_story_backend/social_story/orchestrator.py`)

- **MP4 header validation**: Check if the received file has a valid MP4 header
- **Better error detection**: Detect corrupted files before attempting to use them
- **Enhanced logging**: More detailed logging around render worker communication
- **Progress tracking**: Log streaming progress to identify where issues occur

### 3. Improved Main App (`social_story_backend/social_story/app.py`)

- **File validation**: Validate files before streaming (size, existence)
- **Better error handling**: Improved error logging and cleanup
- **Streaming safety**: Added safety checks during streaming

### 4. Enhanced Health Checks (`render_worker/app.py`)

- **FFmpeg validation**: Check if FFmpeg is working properly
- **System information**: Provide debugging information about the worker environment

## Testing and Validation

### Debug Script

Created `scripts/debug_video_issue.py` to:
- Test the video generation pipeline locally
- Validate MP4 headers and file integrity
- Check FFmpeg functionality
- Provide detailed debugging information

### Usage

```bash
cd scripts
python3 debug_video_issue.py
```

## Prevention Measures

### 1. File Validation

- Check file size before streaming (must be > 1KB)
- Validate MP4 headers
- Use FFprobe for additional validation

### 2. Memory Management

- Stream from memory instead of file handles
- Clean up temporary files before streaming
- Avoid file handle conflicts

### 3. Error Handling

- Graceful fallback to local FFmpeg rendering
- Detailed error logging
- Proper cleanup on failures

### 4. Monitoring

- Enhanced logging throughout the pipeline
- Progress tracking for streaming operations
- Health check endpoints for services

## Deployment Notes

### For Production

1. **Deploy the render worker first** with the fixes
2. **Test the health endpoint**: `GET /health` should show FFmpeg as available
3. **Monitor logs** for any streaming issues
4. **Verify file sizes** are in the expected range (1000-1500 KB)

### Rollback Plan

If issues persist:
1. Disable external render worker by setting `RENDER_WORKER_URL=""`
2. Fall back to local FFmpeg rendering
3. Investigate render worker logs for specific errors

## Expected Results

After applying these fixes:

- ✅ MP4 files should be complete (1000-1500 KB)
- ✅ No more 26-byte corrupted files
- ✅ Better error messages and logging
- ✅ Graceful fallback to local rendering if needed
- ✅ Improved reliability in serverless environments

## Monitoring

Watch for these log messages to confirm the fix is working:

```
INFO: Finished receiving from render worker: X chunks, Y total bytes
INFO: Worker video size validation passed: X bytes
INFO: Successfully streamed video file: /path/to/video.mp4
```

## Related Issues

This fix addresses the memory mentioned in the rules about asyncio background tasks being killed in serverless environments. By reading files into memory before streaming and avoiding file handle dependencies, we ensure the video data is preserved even if the serverless context is terminated.
