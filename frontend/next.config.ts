import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Static export for Vercel + FastAPI deployment
  // This generates plain HTML files that FastAPI can serve
  output: 'export',

  // Output directory for static files (relative to project root)
  distDir: 'out',

  // Proxy API requests to FastAPI backend in development
  async rewrites() {
    if (process.env.NODE_ENV === 'production') {
      return [];
    }
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },

  // Disable image optimization (not needed for static export)
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
