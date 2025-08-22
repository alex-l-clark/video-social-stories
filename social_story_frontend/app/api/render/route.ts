import { NextRequest, NextResponse } from 'next/server';

// Force Node.js runtime for better video handling
export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
export const maxDuration = 300; // 5 minutes for video rendering

const BACKEND_RENDER_URL = process.env.BACKEND_RENDER_URL || 'http://localhost:8000';
const MIN_RENDER_BYTES = parseInt(process.env.MIN_RENDER_BYTES || '500000');
const RENDER_FETCH_ATTEMPTS = parseInt(process.env.RENDER_FETCH_ATTEMPTS || '3');
const RENDER_RETRY_DELAY_MS = parseInt(process.env.RENDER_RETRY_DELAY_MS || '1200');
const USE_DIRECT_DOWNLOAD = process.env.USE_DIRECT_DOWNLOAD === 'true';

interface RenderResponse {
  url?: string;
  size?: number;
  [key: string]: any;
}

function generateRequestId(): string {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

async function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function fetchWithRetry(
  url: string, 
  options: RequestInit, 
  requestId: string,
  attempt: number = 1
): Promise<{ response: Response; buffer: Buffer; size: number }> {
  console.log(`[${requestId}] Attempt ${attempt}/${RENDER_FETCH_ATTEMPTS}: Fetching ${url}`);
  
  const startTime = Date.now();
  
  try {
    const response = await fetch(url, options);
    const duration = Date.now() - startTime;
    
    console.log(`[${requestId}] Backend response: ${response.status} ${response.statusText} (${duration}ms)`);
    
    if (!response.ok) {
      throw new Error(`Backend error: ${response.status} ${response.statusText}`);
    }
    
    // Buffer the full response
    const arrayBuffer = await response.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);
    const size = buffer.length;
    
    console.log(`[${requestId}] Received ${size} bytes from backend`);
    
    // Validate size
    if (size < MIN_RENDER_BYTES) {
      const errorMsg = `Response too small: ${size} bytes (expected >= ${MIN_RENDER_BYTES})`;
      console.warn(`[${requestId}] ${errorMsg}`);
      
      if (attempt < RENDER_FETCH_ATTEMPTS) {
        console.log(`[${requestId}] Retrying in ${RENDER_RETRY_DELAY_MS}ms...`);
        await sleep(RENDER_RETRY_DELAY_MS);
        return fetchWithRetry(url, options, requestId, attempt + 1);
      } else {
        throw new Error(errorMsg);
      }
    }
    
    console.log(`[${requestId}] Successfully fetched video: ${size} bytes in ${duration}ms`);
    return { response, buffer, size };
    
  } catch (error) {
    const duration = Date.now() - startTime;
    console.error(`[${requestId}] Attempt ${attempt} failed after ${duration}ms:`, error);
    
    if (attempt < RENDER_FETCH_ATTEMPTS) {
      console.log(`[${requestId}] Retrying in ${RENDER_RETRY_DELAY_MS}ms...`);
      await sleep(RENDER_RETRY_DELAY_MS);
      return fetchWithRetry(url, options, requestId, attempt + 1);
    } else {
      throw error;
    }
  }
}

export async function GET(request: NextRequest) {
  const requestId = generateRequestId();
  const { searchParams } = new URL(request.url);
  
  console.log(`[${requestId}] MP4 render request started`);
  console.log(`[${requestId}] Query params:`, Object.fromEntries(searchParams.entries()));
  
  try {
    // Build backend URL
    const backendUrl = `${BACKEND_RENDER_URL}/v1/jobs/${searchParams.get('job_id')}/download`;
    
    if (!searchParams.get('job_id')) {
      return NextResponse.json(
        { error: 'Missing job_id parameter', requestId }, 
        { status: 400 }
      );
    }
    
    // Prepare fetch options with timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 280_000); // 280 seconds
    
    const fetchOptions: RequestInit = {
      method: 'GET',
      cache: 'no-store',
      signal: controller.signal,
      headers: {
        'X-Request-ID': requestId,
        'User-Agent': 'video-social-stories-frontend/1.0',
      },
    };
    
    try {
      const { response, buffer, size } = await fetchWithRetry(backendUrl, fetchOptions, requestId);
      
      clearTimeout(timeoutId);
      
      // Check for direct download mode (JSON response with signed URL)
      const contentType = response.headers.get('content-type') || '';
      
      if (USE_DIRECT_DOWNLOAD && contentType.includes('application/json')) {
        try {
          const jsonData: RenderResponse = JSON.parse(buffer.toString());
          if (jsonData.url && jsonData.size && jsonData.size >= MIN_RENDER_BYTES) {
            console.log(`[${requestId}] Direct download mode: redirecting to ${jsonData.url}`);
            return NextResponse.redirect(jsonData.url, { status: 303 });
          }
        } catch (jsonError) {
          console.warn(`[${requestId}] Failed to parse JSON response, falling back to proxy mode`);
        }
      }
      
      // Return MP4 with proper headers
      const headers = new Headers();
      headers.set('Content-Type', 'video/mp4');
      headers.set('Content-Length', size.toString());
      headers.set('Cache-Control', 'no-store');
      headers.set('Accept-Ranges', 'bytes');
      headers.set('X-Request-ID', requestId);
      
      // Preserve original filename if available
      const disposition = response.headers.get('content-disposition');
      if (disposition) {
        headers.set('Content-Disposition', disposition);
      }
      
      console.log(`[${requestId}] Streaming MP4 response: ${size} bytes`);
      
      return new NextResponse(buffer, {
        status: 200,
        headers,
      });
      
    } finally {
      clearTimeout(timeoutId);
    }
    
  } catch (error) {
    console.error(`[${requestId}] MP4 render failed:`, error);
    
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    
    return NextResponse.json(
      { 
        error: 'Video render failed', 
        details: errorMessage,
        requestId,
        minBytes: MIN_RENDER_BYTES,
        attempts: RENDER_FETCH_ATTEMPTS
      }, 
      { status: 502 }
    );
  }
}

export async function POST(request: NextRequest) {
  // Handle POST requests for starting render jobs
  const requestId = generateRequestId();
  console.log(`[${requestId}] POST render request started`);
  
  try {
    const body = await request.json();
    const backendUrl = `${BACKEND_RENDER_URL}/v1/social-story:start`;
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Request-ID': requestId,
      },
      body: JSON.stringify(body),
      cache: 'no-store',
      signal: AbortSignal.timeout(300_000), // 5 minutes
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(`Backend error: ${response.status} ${response.statusText}`);
    }
    
    console.log(`[${requestId}] Render job started: ${data.job_id}`);
    
    return NextResponse.json({
      ...data,
      requestId,
    });
    
  } catch (error) {
    console.error(`[${requestId}] POST render failed:`, error);
    
    return NextResponse.json(
      { 
        error: 'Failed to start render job', 
        details: error instanceof Error ? error.message : 'Unknown error',
        requestId 
      }, 
      { status: 502 }
    );
  }
}