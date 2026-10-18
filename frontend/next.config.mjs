/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      // 1. Go Auth Microservice (Port 8081)
      {
        source: '/api/auth/:path*',
        destination: 'http://127.0.0.1:8081/api/v1/auth/:path*',
      },
      // 2. Express Interaction Microservice (Port 8082)
      {
        source: '/api/interactions/:path*',
        destination: 'http://127.0.0.1:8082/api/v1/interactions/:path*',
      },
      // 3. Rust Scoring Microservice (Port 8083)
      {
        source: '/api/score/:path*',
        destination: 'http://127.0.0.1:8083/api/v1/score/:path*',
      },
      // 4. Python FastAPI Microservice (Port 8000)
      {
        source: '/api/python/:path*',
        destination: 'http://127.0.0.1:8000/api/v1/:path*',
      },
    ];
  },
};

export default nextConfig;
