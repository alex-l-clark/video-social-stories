'use client';

import { useState } from 'react';
import { downloadMp4FromRoute, getDownloadCapabilities } from '../utils/downloadMp4';

export default function Home() {
  const [jobId, setJobId] = useState('');
  const [downloading, setDownloading] = useState(false);
  const [result, setResult] = useState<string>('');
  
  const capabilities = getDownloadCapabilities();
  
  const handleDownload = async () => {
    if (!jobId.trim()) {
      setResult('Please enter a job ID');
      return;
    }
    
    setDownloading(true);
    setResult('Starting download...');
    
    try {
      const downloadResult = await downloadMp4FromRoute(`job_id=${jobId.trim()}`);
      
      if (downloadResult.success) {
        setResult(`✅ Download successful! ${downloadResult.bytes} bytes (Request: ${downloadResult.requestId})`);
      } else {
        setResult(`❌ Download failed: ${downloadResult.error}`);
      }
    } catch (error) {
      setResult(`❌ Download error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setDownloading(false);
    }
  };

  const handleSmokeTest = async () => {
    setResult('Running smoke test...');
    
    try {
      const response = await fetch('/api/render-smoke', {
        cache: 'no-store',
      });
      
      const data = await response.json();
      
      if (data.ok) {
        setResult(`✅ Smoke test passed!\nBytes: ${data.bytes}\nDuration: ${data.durationMs}ms\nRequest ID: ${data.requestId}`);
      } else {
        setResult(`❌ Smoke test failed: ${data.error}\nRequest ID: ${data.requestId}`);
      }
    } catch (error) {
      setResult(`❌ Smoke test error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };
  
  return (
    <main style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <h1>Video Social Stories</h1>
      <p>Download your personalized video stories with mobile optimization 🎬</p>
      
      <div style={{ marginBottom: '2rem' }}>
        <h2>System Info</h2>
        <ul>
          <li>Mobile device: {capabilities.isMobile ? 'Yes' : 'No'}</li>
          <li>iOS device: {capabilities.isIOS ? 'Yes' : 'No'}</li>
          <li>Download support: {capabilities.supportsDownload ? 'Yes' : 'No'}</li>
        </ul>
        
        {capabilities.recommendations.length > 0 && (
          <div>
            <h3>Download Tips:</h3>
            <ul>
              {capabilities.recommendations.map((tip, index) => (
                <li key={index}>{tip}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
      
      <div style={{ marginBottom: '2rem' }}>
        <h2>Download Video</h2>
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
          <input
            type="text"
            placeholder="Enter job ID"
            value={jobId}
            onChange={(e) => setJobId(e.target.value)}
            style={{ flex: 1, minWidth: '200px', padding: '0.5rem', fontSize: '1rem' }}
          />
          <button
            onClick={handleDownload}
            disabled={downloading}
            style={{
              padding: '0.5rem 1rem',
              fontSize: '1rem',
              backgroundColor: downloading ? '#ccc' : '#007cba',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: downloading ? 'not-allowed' : 'pointer',
            }}
          >
            {downloading ? 'Downloading...' : 'Download MP4'}
          </button>
          <button
            onClick={handleSmokeTest}
            style={{
              padding: '0.5rem 1rem',
              fontSize: '1rem',
              backgroundColor: '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            Run Smoke Test
          </button>
        </div>
        
        {result && (
          <div style={{
            padding: '1rem',
            backgroundColor: result.startsWith('✅') ? '#d4edda' : result.startsWith('❌') ? '#f8d7da' : '#d1ecf1',
            border: '1px solid',
            borderColor: result.startsWith('✅') ? '#c3e6cb' : result.startsWith('❌') ? '#f5c6cb' : '#bee5eb',
            borderRadius: '4px',
            marginTop: '1rem',
            fontFamily: 'monospace',
            whiteSpace: 'pre-wrap',
            fontSize: '0.9rem',
          }}>
            {result}
          </div>
        )}
      </div>
      
      <div style={{ marginBottom: '2rem' }}>
        <h2>API Endpoints</h2>
        <ul>
          <li><code>GET /api/render?job_id=...</code> - Download MP4 (hardened proxy route)</li>
          <li><code>POST /api/render</code> - Start render job</li>
          <li><code>GET /api/render-smoke</code> - Smoke test (creates test video)</li>
        </ul>
      </div>

      <div>
        <h2>Features</h2>
        <ul>
          <li>✅ Node.js runtime with 5-minute timeout</li>
          <li>✅ Full buffering with retry logic (up to 3 attempts)</li>
          <li>✅ Size validation (minimum 500KB)</li>
          <li>✅ Proper MP4 headers (Content-Type, Content-Length, Accept-Ranges)</li>
          <li>✅ Mobile-optimized downloads (iOS Safari & Android Chrome)</li>
          <li>✅ Correlation IDs for request tracing</li>
          <li>✅ Optional direct download mode (feature-flagged)</li>
        </ul>
      </div>
    </main>
  );
}