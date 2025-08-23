/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // Produce a fully static site (for Render "runtime: static")
  output: 'export',

  // If you use next/image, disable the optimization server
  images: { unoptimized: true },

  // Make the backend URL available at build time for the client bundle
  // Prefer NEXT_PUBLIC_API_URL; keep compatibility with your old name.
  env: {
    NEXT_PUBLIC_API_URL:
      process.env.NEXT_PUBLIC_API_URL ||
      process.env.NEXT_PUBLIC_BACKEND_URL ||
      'http://localhost:8000',
  },

  // (Optional) add this if you use dynamic routes and want /path/ -> /path/index.html
  // trailingSlash: true,
};

module.exports = nextConfig;
