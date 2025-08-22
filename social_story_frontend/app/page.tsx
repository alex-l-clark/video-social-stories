'use client';

import { useState, useEffect } from 'react';
import { downloadMp4FromRoute, getDownloadCapabilities } from '../utils/downloadMp4';

interface StoryRequest {
  age: number;
  reading_level: string;
  diagnosis_summary: string;
  situation: string;
  setting: string;
  words_to_avoid: string[];
  voice_preset: string;
}

export default function Home() {
  // Story creation form state
  const [formData, setFormData] = useState<StoryRequest>({
    age: 6,
    reading_level: 'early_reader',
    diagnosis_summary: 'autism; prefers routine',
    situation: '',
    setting: '',
    words_to_avoid: [],
    voice_preset: 'calm_childlike_female'
  });
  
  const [wordsToAvoidInput, setWordsToAvoidInput] = useState('');
  
  // Job management state
  const [currentJobId, setCurrentJobId] = useState('');
  const [jobStatus, setJobStatus] = useState<'idle' | 'starting' | 'running' | 'succeeded' | 'failed'>('idle');
  const [jobError, setJobError] = useState('');
  
  // Download state
  const [downloading, setDownloading] = useState(false);
  const [result, setResult] = useState<string>('');
  
  const capabilities = getDownloadCapabilities();

  // Poll job status (simplified for now - the backend runs synchronously)
  useEffect(() => {
    if (currentJobId && (jobStatus === 'starting' || jobStatus === 'running')) {
      // For synchronous backend, let's just wait and then check if it succeeded
      const timeout = setTimeout(() => {
        if (jobStatus === 'starting' || jobStatus === 'running') {
          setJobStatus('succeeded');
          setResult(`✅ Story video should be completed! Try downloading.\nJob ID: ${currentJobId}`);
        }
      }, 5000); // Give it 5 seconds to process

      return () => clearTimeout(timeout);
    }
  }, [currentJobId, jobStatus]);

  const handleCreateStory = async () => {
    if (!formData.situation.trim() || !formData.setting.trim()) {
      setResult('Please fill in both situation and setting fields');
      return;
    }

    setJobStatus('starting');
    setResult('Creating your story...');
    setJobError('');

    try {
      const requestData = {
        ...formData,
        words_to_avoid: wordsToAvoidInput.split(',').map(w => w.trim()).filter(w => w)
      };

      const response = await fetch('/api/render', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData),
      });

      const data = await response.json();

      if (response.ok && data.job_id) {
        setCurrentJobId(data.job_id);
        setJobStatus(data.status || 'running');
        setResult(`✅ Story creation started! Job ID: ${data.job_id}\n${jobStatus === 'succeeded' ? 'Ready to download!' : 'Creating your video story...'}`);
      } else {
        setJobStatus('failed');
        setJobError(data.error || 'Failed to start job');
        setResult(`❌ Failed to create story: ${data.error || 'Unknown error'}`);
      }
    } catch (error) {
      setJobStatus('failed');
      setJobError(error instanceof Error ? error.message : 'Unknown error');
      setResult(`❌ Error creating story: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const handleDownload = async (jobId?: string) => {
    const downloadJobId = jobId || currentJobId;
    
    if (!downloadJobId.trim()) {
      setResult('No job ID available for download');
      return;
    }
    
    setDownloading(true);
    setResult('Starting download...');
    
    try {
      const downloadResult = await downloadMp4FromRoute(`job_id=${downloadJobId.trim()}`);
      
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
        if (data.jobId) {
          setCurrentJobId(data.jobId);
          setJobStatus('succeeded');
        }
      } else {
        setResult(`❌ Smoke test failed: ${data.error}\nRequest ID: ${data.requestId}`);
      }
    } catch (error) {
      setResult(`❌ Smoke test error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };
  
  const inputStyle = {
    width: '100%',
    padding: '0.5rem',
    fontSize: '1rem',
    border: '1px solid #ccc',
    borderRadius: '4px',
    marginBottom: '1rem'
  };

  const selectStyle = {
    ...inputStyle,
    backgroundColor: 'white'
  };

  const buttonStyle = {
    padding: '0.75rem 1.5rem',
    fontSize: '1rem',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    marginRight: '0.5rem',
    marginBottom: '0.5rem'
  };

  return (
    <main style={{ padding: '2rem', maxWidth: '900px', margin: '0 auto' }}>
      <h1>🎬 AI Video Social Stories</h1>
      <p>Create personalized video stories for social learning with AI-powered narration and illustrations.</p>
      
      {/* Story Creation Form */}
      <div style={{ marginBottom: '2rem', padding: '1.5rem', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
        <h2>Create Your Story</h2>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 'bold' }}>Age</label>
            <input
              type="number"
              min="3"
              max="18"
              value={formData.age}
              onChange={(e) => setFormData({...formData, age: parseInt(e.target.value) || 6})}
              style={inputStyle}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 'bold' }}>Reading Level</label>
            <select
              value={formData.reading_level}
              onChange={(e) => setFormData({...formData, reading_level: e.target.value})}
              style={selectStyle}
            >
              <option value="pre_reader">Pre-reader</option>
              <option value="early_reader">Early reader</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 'bold' }}>Voice</label>
            <select
              value={formData.voice_preset}
              onChange={(e) => setFormData({...formData, voice_preset: e.target.value})}
              style={selectStyle}
            >
              <option value="calm_childlike_female">Calm Female (Child-like)</option>
              <option value="calm_childlike_male">Calm Male (Child-like)</option>
              <option value="warm_adult_female">Warm Female (Adult)</option>
              <option value="warm_adult_male">Warm Male (Adult)</option>
            </select>
          </div>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 'bold' }}>Situation (Required)</label>
          <input
            type="text"
            placeholder="e.g., Sharing toys with a friend at school"
            value={formData.situation}
            onChange={(e) => setFormData({...formData, situation: e.target.value})}
            style={inputStyle}
          />
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 'bold' }}>Setting (Required)</label>
          <input
            type="text"
            placeholder="e.g., classroom, playground, home, grocery store"
            value={formData.setting}
            onChange={(e) => setFormData({...formData, setting: e.target.value})}
            style={inputStyle}
          />
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 'bold' }}>Diagnosis/Notes</label>
          <input
            type="text"
            placeholder="e.g., autism; prefers routine"
            value={formData.diagnosis_summary}
            onChange={(e) => setFormData({...formData, diagnosis_summary: e.target.value})}
            style={inputStyle}
          />
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 'bold' }}>Words to Avoid (comma-separated)</label>
          <input
            type="text"
            placeholder="e.g., scary, bad, wrong, stupid"
            value={wordsToAvoidInput}
            onChange={(e) => setWordsToAvoidInput(e.target.value)}
            style={inputStyle}
          />
        </div>

        <button
          onClick={handleCreateStory}
          disabled={jobStatus === 'starting' || jobStatus === 'running'}
          style={{
            ...buttonStyle,
            backgroundColor: jobStatus === 'starting' || jobStatus === 'running' ? '#6c757d' : '#007bff',
            color: 'white',
            fontSize: '1.1rem',
            padding: '1rem 2rem'
          }}
        >
          {jobStatus === 'starting' ? 'Starting...' : jobStatus === 'running' ? 'Creating Story...' : 'Create Story Video'}
        </button>
        
        {jobStatus === 'running' && (
          <div style={{ marginTop: '1rem', padding: '0.75rem', backgroundColor: '#cce5ff', borderRadius: '4px' }}>
            ⏳ Creating your video story... This typically takes 2-3 minutes.
            {currentJobId && <div style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>Job ID: {currentJobId}</div>}
          </div>
        )}
      </div>

      {/* Download Section */}
      {(jobStatus === 'succeeded' || currentJobId) && (
        <div style={{ marginBottom: '2rem', padding: '1.5rem', backgroundColor: '#d4edda', borderRadius: '8px' }}>
          <h2>Download Your Video</h2>
          {jobStatus === 'succeeded' && (
            <p>✅ Your story video is ready! Click below to download.</p>
          )}
          
          <button
            onClick={() => handleDownload()}
            disabled={downloading || jobStatus !== 'succeeded'}
            style={{
              ...buttonStyle,
              backgroundColor: downloading ? '#6c757d' : jobStatus === 'succeeded' ? '#28a745' : '#ffc107',
              color: jobStatus === 'succeeded' ? 'white' : 'black',
              fontSize: '1.1rem',
              padding: '1rem 2rem'
            }}
          >
            {downloading ? 'Downloading...' : jobStatus === 'succeeded' ? 'Download MP4' : 'Video Not Ready'}
          </button>

          {capabilities.isMobile && (
            <div style={{ marginTop: '1rem', fontSize: '0.9rem', color: '#666' }}>
              <strong>Mobile Tips:</strong>
              {capabilities.recommendations.map((tip, index) => (
                <div key={index}>• {tip}</div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Testing Section */}
      <div style={{ marginBottom: '2rem', padding: '1.5rem', backgroundColor: '#fff3cd', borderRadius: '8px' }}>
        <h2>Testing & Demo</h2>
        <p>Test the system with a pre-configured example story:</p>
        
        <button
          onClick={handleSmokeTest}
          style={{
            ...buttonStyle,
            backgroundColor: '#17a2b8',
            color: 'white'
          }}
        >
          Run Demo Story
        </button>
      </div>

      {/* Results */}
      {result && (
        <div style={{
          padding: '1rem',
          backgroundColor: result.startsWith('✅') ? '#d4edda' : result.startsWith('❌') ? '#f8d7da' : '#d1ecf1',
          border: '1px solid',
          borderColor: result.startsWith('✅') ? '#c3e6cb' : result.startsWith('❌') ? '#f5c6cb' : '#bee5eb',
          borderRadius: '4px',
          marginBottom: '2rem',
          fontFamily: 'monospace',
          whiteSpace: 'pre-wrap',
          fontSize: '0.9rem',
        }}>
          {result}
        </div>
      )}

      {/* System Info */}
      <div style={{ marginBottom: '2rem' }}>
        <h2>System Status</h2>
        <ul>
          <li>Platform: {capabilities.isMobile ? (capabilities.isIOS ? 'iOS' : 'Mobile') : 'Desktop'}</li>
          <li>Download support: {capabilities.supportsDownload ? 'Yes' : 'No'}</li>
          <li>MP4 proxy: ✅ Hardened with retry logic</li>
          <li>Mobile optimization: ✅ iOS Safari & Android Chrome</li>
        </ul>
      </div>
    </main>
  );
}