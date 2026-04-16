import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
   output: 'export', // This tells Next.js to generate static files
  trailingSlash: true, // Optional: recommended for easier static hosting
  images: {
    unoptimized: true, // Static export doesn't support Next's image optimization
  },
  // devIndicators: false,
};

export default nextConfig;
