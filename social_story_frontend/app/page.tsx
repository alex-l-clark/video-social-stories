export default function Home() {
  return (
    <main style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <h1>Video Social Stories</h1>
      <p>Frontend deployment successful! 🎉</p>
      
      <div style={{ marginBottom: '2rem' }}>
        <h2>Build Status</h2>
        <p>✅ Next.js build completed</p>
        <p>✅ TypeScript compilation successful</p>
        <p>✅ Ready for MP4 functionality</p>
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