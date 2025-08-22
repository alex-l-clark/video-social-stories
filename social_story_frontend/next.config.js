/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    // Enable latest features for better performance
  },
  async rewrites() {
    return [
      // Optional: Proxy other backend routes if needed
      {
        source: '/api/health',
        destination: `${process.env.BACKEND_RENDER_URL || 'http://localhost:8000'}/health`,
      },
    ];
  },
};

module.exports = nextConfig;