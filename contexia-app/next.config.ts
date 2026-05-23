import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  trailingSlash: false,
  images: {
    unoptimized: true,
  },
  async redirects() {
    return [
      {
        source: '/:path*',
        destination: 'https://contexia.online/app/',
        permanent: false,
      },
    ];
  },
};

export default nextConfig;
