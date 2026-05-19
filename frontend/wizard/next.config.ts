import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // NO static export — we need API routes (leads, email, audit)
  // basePath keeps assets working when proxied from contexia.online/wizard
  basePath: "/wizard",
  trailingSlash: true,
  images: {
    unoptimized: true,
    remotePatterns: [
      {
        protocol: "https",
        hostname: "www.contexia.online",
      },
    ],
  },
};

export default nextConfig;
