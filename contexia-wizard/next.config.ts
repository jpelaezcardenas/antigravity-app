import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  basePath: "/wizard",
  trailingSlash: false,
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
