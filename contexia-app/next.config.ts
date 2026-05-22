import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Remove "export" to allow server-side features (redirect, etc.) on Vercel
  trailingSlash: false,
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
