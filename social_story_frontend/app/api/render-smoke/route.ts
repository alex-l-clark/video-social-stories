import { NextRequest, NextResponse } from 'next/server';

// Force Node.js runtime
export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
export const maxDuration = 300;

const BACKEND_RENDER_URL = process.env.BACKEND_RENDER_URL || 'http://localhost:8000';
const MIN_RENDER_BYTES = parseInt(process.env.MIN_RENDER_BYTES || '500000');

// Test story parameters
const TEST_STORY_REQUEST = {
  situation: "Sharing toys with a friend at school",
  setting: "classroom",
  age: 6,
  reading_level: "beginner",
  diagnosis_summary: "Autism, needs clear social expectations",
  words_to_avoid: ["scary", "bad", "wrong"],
  voice_preset: "calm_child_friendly"
};

function generateRequestId(): string {
  return 'smoke-' + Date.now().toString(36) + Math.random().toString(36).substr(2);
}

export async function GET(request: NextRequest) {
  const requestId = generateRequestId();
  const startTime = Date.now();
  
  console.log(`[${requestId}] Smoke test started`);
  
  try {
    // Step 1: Start a render job
    console.log(`[${requestId}] Starting test render job...`);
    
    const startJobResponse = await fetch(`${BACKEND_RENDER_URL}/v1/social-story:start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Request-ID': requestId,
      },
      body: JSON.stringify(TEST_STORY_REQUEST),
      cache: 'no-store',
      signal: AbortSignal.timeout(280_000),
    });
    
    if (!startJobResponse.ok) {
      throw new Error(`Failed to start job: ${startJobResponse.status} ${startJobResponse.statusText}`);
    }
    
    const jobData = await startJobResponse.json();
    const jobId = jobData.job_id;
    
    if (!jobId) {
      throw new Error('No job_id returned from backend');
    }
    
    console.log(`[${requestId}] Test job started: ${jobId}`);
    
    // Step 2: Wait for job completion (for synchronous backend)
    let attempts = 0;
    const maxAttempts = 60; // 5 minutes max
    
    while (attempts < maxAttempts) {
      const statusResponse = await fetch(`${BACKEND_RENDER_URL}/v1/jobs/${jobId}`, {
        cache: 'no-store',
      });
      
      if (!statusResponse.ok) {
        throw new Error(`Failed to check job status: ${statusResponse.status}`);
      }
      
      const status = await statusResponse.json();
      console.log(`[${requestId}] Job status: ${status.status}`);
      
      if (status.status === 'succeeded') {
        break;
      } else if (status.status === 'failed') {
        throw new Error(`Job failed: ${status.error}`);
      }
      
      // Wait 5 seconds before checking again
      await new Promise(resolve => setTimeout(resolve, 5000));
      attempts++;
    }
    
    if (attempts >= maxAttempts) {
      throw new Error('Job timed out');
    }
    
    // Step 3: Test the download endpoint
    console.log(`[${requestId}] Testing download endpoint...`);
    
    const downloadStartTime = Date.now();
    const downloadResponse = await fetch(`${BACKEND_RENDER_URL}/v1/jobs/${jobId}/download`, {
      cache: 'no-store',
      signal: AbortSignal.timeout(30_000),
    });
    
    if (!downloadResponse.ok) {
      throw new Error(`Download failed: ${downloadResponse.status} ${downloadResponse.statusText}`);
    }
    
    // Check response size
    const arrayBuffer = await downloadResponse.arrayBuffer();
    const bytes = arrayBuffer.byteLength;
    const downloadDuration = Date.now() - downloadStartTime;
    
    console.log(`[${requestId}] Download completed: ${bytes} bytes in ${downloadDuration}ms`);
    
    // Validate size
    const sizeOk = bytes >= MIN_RENDER_BYTES;
    const totalDuration = Date.now() - startTime;
    
    const result = {
      ok: sizeOk,
      bytes,
      durationMs: totalDuration,
      downloadDurationMs: downloadDuration,
      attempts: 1, // Single attempt for smoke test
      requestId,
      jobId,
      minBytesRequired: MIN_RENDER_BYTES,
      contentType: downloadResponse.headers.get('content-type'),
    };
    
    console.log(`[${requestId}] Smoke test completed:`, result);
    
    return NextResponse.json(result, { 
      status: sizeOk ? 200 : 500,
      headers: {
        'X-Request-ID': requestId,
      },
    });
    
  } catch (error) {
    const totalDuration = Date.now() - startTime;
    const errorDetails = error instanceof Error ? error.message : 'Unknown error';
    
    console.error(`[${requestId}] Smoke test failed after ${totalDuration}ms:`, error);
    
    return NextResponse.json({
      ok: false,
      error: errorDetails,
      durationMs: totalDuration,
      requestId,
      minBytesRequired: MIN_RENDER_BYTES,
    }, { 
      status: 500,
      headers: {
        'X-Request-ID': requestId,
      },
    });
  }
}