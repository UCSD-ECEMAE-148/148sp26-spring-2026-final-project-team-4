import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: ['10.215.180.60'],
  turbopack: {
    root: __dirname,
  },
};

export default nextConfig;