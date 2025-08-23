const origin = process.env.NEXT_PUBLIC_BACKEND_ORIGIN || "";
const backendUrl = origin ? `${origin.replace(/\/+$/, "")}/api` : "/api";

module.exports = {
  reactStrictMode: true,
  images: { unoptimized: true },
  output: 'export', 
  env: {
    NEXT_PUBLIC_BACKEND_URL:
      process.env.NEXT_PUBLIC_BACKEND_URL || backendUrl
  }
};

