/**
 * Mobile-friendly MP4 download utility
 * 
 * This utility ensures downloads work reliably on mobile devices,
 * especially iOS Safari which has strict requirements for downloads.
 */

export interface DownloadOptions {
  filename?: string;
  minSize?: number;
  timeout?: number;
}

export interface DownloadResult {
  success: boolean;
  bytes?: number;
  error?: string;
  requestId?: string;
}

/**
 * Downloads MP4 from the render API route with mobile optimizations
 * 
 * IMPORTANT: This function must be called within a user gesture (click/tap)
 * to satisfy iOS Safari security requirements.
 * 
 * @param queryString Query parameters for the render API (e.g., "job_id=123")
 * @param options Download options
 * @returns Promise with download result
 */
export async function downloadMp4FromRoute(
  queryString: string, 
  options: DownloadOptions = {}
): Promise<DownloadResult> {
  const {
    filename = 'story.mp4',
    minSize = 500_000,
    timeout = 300_000, // 5 minutes
  } = options;
  
  try {
    console.log('Starting MP4 download:', { queryString, filename, minSize });
    
    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    try {
      // Fetch from our hardened API route
      const response = await fetch(`/api/render?${queryString}`, {
        cache: 'no-store',
        signal: controller.signal,
        headers: {
          'Accept': 'video/mp4',
        },
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.error || 
          errorData.details || 
          `HTTP ${response.status}: ${response.statusText}`
        );
      }
      
      // Convert to blob for download
      const blob = await response.blob();
      const bytes = blob.size;
      const requestId = response.headers.get('X-Request-ID') || 'unknown';
      
      console.log('MP4 downloaded:', { bytes, requestId, contentType: blob.type });
      
      // Validate size
      if (bytes < minSize) {
        throw new Error(`Video too small: ${bytes} bytes (expected >= ${minSize})`);
      }
      
      // Create download link and trigger download
      const url = URL.createObjectURL(blob);
      
      try {
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        
        // Ensure link is added to DOM for iOS Safari
        document.body.appendChild(link);
        
        // Trigger download
        link.click();
        
        // Clean up
        document.body.removeChild(link);
        
        console.log('Download triggered successfully');
        
        return {
          success: true,
          bytes,
          requestId,
        };
        
      } finally {
        // Always clean up the object URL
        URL.revokeObjectURL(url);
      }
      
    } finally {
      clearTimeout(timeoutId);
    }
    
  } catch (error) {
    console.error('MP4 download failed:', error);
    
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    
    return {
      success: false,
      error: errorMessage,
    };
  }
}

/**
 * Creates a video preview element from the downloaded blob
 * Useful for showing a preview before download
 * 
 * @param queryString Query parameters for the render API
 * @returns Promise with video element or error
 */
export async function createVideoPreview(queryString: string): Promise<{
  success: boolean;
  videoElement?: HTMLVideoElement;
  error?: string;
}> {
  try {
    const response = await fetch(`/api/render?${queryString}`, {
      cache: 'no-store',
      headers: {
        'Accept': 'video/mp4',
      },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch video: ${response.status}`);
    }
    
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    
    const video = document.createElement('video');
    video.src = url;
    video.controls = true;
    video.playsInline = true; // Important for iOS
    video.style.maxWidth = '100%';
    video.style.height = 'auto';
    
    // Clean up URL when video is loaded or errors
    const cleanup = () => URL.revokeObjectURL(url);
    video.addEventListener('loadeddata', cleanup, { once: true });
    video.addEventListener('error', cleanup, { once: true });
    
    return {
      success: true,
      videoElement: video,
    };
    
  } catch (error) {
    console.error('Video preview failed:', error);
    
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Utility to check if the current environment supports reliable downloads
 * Useful for showing appropriate UI messages
 */
export function getDownloadCapabilities(): {
  supportsDownload: boolean;
  isMobile: boolean;
  isIOS: boolean;
  recommendations: string[];
} {
  const userAgent = navigator.userAgent.toLowerCase();
  const isMobile = /mobile|android|iphone|ipad|ipod/.test(userAgent);
  const isIOS = /iphone|ipad|ipod/.test(userAgent);
  const isAndroid = /android/.test(userAgent);
  
  const recommendations: string[] = [];
  
  if (isIOS) {
    recommendations.push('Tap and hold the download button to save the video');
    recommendations.push('Videos will open in a new tab - use "Share > Save Video" to save');
  } else if (isAndroid) {
    recommendations.push('Video will download to your Downloads folder');
  } else {
    recommendations.push('Video will download automatically');
  }
  
  return {
    supportsDownload: true, // Modern browsers support blob downloads
    isMobile,
    isIOS,
    recommendations,
  };
}