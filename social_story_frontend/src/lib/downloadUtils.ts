/**
 * Enhanced download utilities with mobile optimization and retry logic
 * This enhances the existing download functionality without breaking the current implementation
 */

export interface DownloadOptions {
  filename?: string;
  minSize?: number;
  maxRetries?: number;
  retryDelay?: number;
}

export interface DownloadResult {
  success: boolean;
  bytes?: number;
  error?: string;
  requestId?: string;
  attempts?: number;
}

export interface DeviceCapabilities {
  isMobile: boolean;
  isIOS: boolean;
  supportsDownload: boolean;
  recommendations: string[];
}

/**
 * Detect device capabilities for download optimization
 */
export function getDeviceCapabilities(): DeviceCapabilities {
  const userAgent = navigator.userAgent.toLowerCase();
  const isMobile = /mobile|android|iphone|ipad|ipod/.test(userAgent);
  const isIOS = /iphone|ipad|ipod/.test(userAgent);
  
  const recommendations: string[] = [];
  
  if (isIOS) {
    recommendations.push('Tap and hold the download button');
    recommendations.push('Use "Share > Save Video" if video opens in new tab');
  } else if (isMobile) {
    recommendations.push('Video will download to your Downloads folder');
    recommendations.push('Check your notifications for download progress');
  } else {
    recommendations.push('Video will download automatically to Downloads');
  }
  
  return {
    isMobile,
    isIOS,
    supportsDownload: true,
    recommendations,
  };
}

/**
 * Enhanced download function with retry logic and mobile optimization
 * This replaces the basic fetch + blob download with a hardened version
 */
export async function downloadVideoWithRetry(
  url: string,
  options: DownloadOptions = {}
): Promise<DownloadResult> {
  const {
    filename = 'social-story-video.mp4',
    minSize = 500_000, // 500KB minimum
    maxRetries = 3,
    retryDelay = 1200,
  } = options;
  
  console.log(`Starting enhanced download: ${url}`);
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      console.log(`Download attempt ${attempt}/${maxRetries}`);
      
      // Fetch with timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 120_000); // 2 minutes
      
      const response = await fetch(url, {
        cache: 'no-store',
        signal: controller.signal,
        headers: {
          'Accept': 'video/mp4',
          'User-Agent': 'social-story-app/1.0',
        },
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      // Get response metadata
      const contentLength = response.headers.get('content-length');
      const requestId = response.headers.get('x-request-id') || 'unknown';
      
      // Convert to blob
      const blob = await response.blob();
      const bytes = blob.size;
      
      console.log(`Downloaded ${bytes} bytes (attempt ${attempt})`);
      
      // Validate size
      if (bytes < minSize) {
        if (attempt < maxRetries) {
          console.warn(`File too small (${bytes} bytes), retrying in ${retryDelay}ms...`);
          await new Promise(resolve => setTimeout(resolve, retryDelay));
          continue;
        } else {
          throw new Error(`Video too small: ${bytes} bytes (expected >= ${minSize})`);
        }
      }
      
      // Validate content type
      if (!blob.type.includes('video') && !blob.type.includes('octet-stream')) {
        throw new Error(`Invalid content type: ${blob.type}`);
      }
      
      // Create download link with mobile optimization
      const downloadUrl = URL.createObjectURL(blob);
      
      try {
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = filename;
        
        // Ensure link is added to DOM for iOS Safari compatibility
        document.body.appendChild(link);
        
        // Trigger download with user gesture
        link.click();
        
        // Clean up
        document.body.removeChild(link);
        
        console.log(`✅ Download successful: ${bytes} bytes`);
        
        return {
          success: true,
          bytes,
          requestId,
          attempts: attempt,
        };
        
      } finally {
        // Always clean up the object URL
        URL.revokeObjectURL(downloadUrl);
      }
      
    } catch (error) {
      console.error(`Download attempt ${attempt} failed:`, error);
      
      if (attempt >= maxRetries) {
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Unknown download error',
          attempts: attempt,
        };
      }
      
      // Wait before retry
      if (attempt < maxRetries) {
        console.log(`Waiting ${retryDelay}ms before retry...`);
        await new Promise(resolve => setTimeout(resolve, retryDelay));
      }
    }
  }
  
  return {
    success: false,
    error: `Failed after ${maxRetries} attempts`,
    attempts: maxRetries,
  };
}

/**
 * Enhanced blob download specifically for mobile devices
 * Handles iOS Safari quirks and provides better error feedback
 */
export async function downloadBlobMobile(
  blob: Blob,
  filename: string,
  minSize: number = 500_000
): Promise<DownloadResult> {
  try {
    const bytes = blob.size;
    
    // Validate size
    if (bytes < minSize) {
      throw new Error(`Video too small: ${bytes} bytes (expected >= ${minSize})`);
    }
    
    // Validate content
    if (!blob.type.includes('video') && !blob.type.includes('octet-stream')) {
      throw new Error(`Invalid content type: ${blob.type}`);
    }
    
    const capabilities = getDeviceCapabilities();
    
    if (capabilities.isIOS) {
      // iOS Safari: Create blob URL and open in new tab
      const url = URL.createObjectURL(blob);
      
      try {
        // Open in new tab - user can then save via Share button
        const newWindow = window.open(url, '_blank');
        
        if (!newWindow) {
          // Fallback: create download link
          const link = document.createElement('a');
          link.href = url;
          link.download = filename;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        }
        
        return {
          success: true,
          bytes,
        };
        
      } finally {
        // Clean up after a delay to allow the download/navigation
        setTimeout(() => URL.revokeObjectURL(url), 5000);
      }
      
    } else {
      // Android/Desktop: Standard download
      const url = URL.createObjectURL(blob);
      
      try {
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        return {
          success: true,
          bytes,
        };
        
      } finally {
        URL.revokeObjectURL(url);
      }
    }
    
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}