import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow server-side fetch to reach the local FastAPI backend
  async rewrites() {
    return [];
  },
};

export default nextConfig;
