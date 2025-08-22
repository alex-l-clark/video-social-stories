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
  
  return (
    <main style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <h1>Video Social Stories</h1>
      <p>Download your personalized video stories</p>
      
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
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
          <input
            type="text"
            placeholder="Enter job ID"
            value={jobId}
            onChange={(e) => setJobId(e.target.value)}
            style={{ flex: 1, padding: '0.5rem', fontSize: '1rem' }}
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
          }}>
            {result}
          </div>
        )}
      </div>
      
      <div>
        <h2>API Endpoints</h2>
        <ul>
          <li><code>GET /api/render?job_id=...</code> - Download MP4</li>
          <li><code>POST /api/render</code> - Start render job</li>
          <li><code>GET /api/render-smoke</code> - Smoke test</li>
        </ul>
      </div>
    </main>
  );
}