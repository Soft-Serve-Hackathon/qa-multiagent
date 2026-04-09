/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  
  // Environment variables for API communication
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  },

  // Server configuration
  serverRuntimeConfig: {
    apiUrl: process.env.API_URL || 'http://backend:8000/api',
  },

  // CORS and rewrites for API calls
  // Uses API_URL (server-side) so Docker inter-container networking works correctly
  async rewrites() {
    const apiUrl = process.env.API_URL || 'http://localhost:8000/api';
    return {
      beforeFiles: [
        {
          source: '/api/:path*',
          destination: `${apiUrl}/:path*`,
        },
      ],
    };
  },
};

module.exports = nextConfig;
