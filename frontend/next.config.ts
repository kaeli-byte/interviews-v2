import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Static export for Vercel + FastAPI deployment
  output: 'export',

  // Disable image optimization (not needed for static export)
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
