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
  async rewrites() {
    return {
      beforeFiles: [
        {
          source: '/api/:path*',
          destination: `${process.env.API_INTERNAL_URL || 'http://backend:8000/api'}/:path*`,
        },
      ],
    };
  },
};

module.exports = nextConfig;
