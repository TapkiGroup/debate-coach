module.exports = {
  reactStrictMode: true,
  images: { unoptimized: true },
  output: 'export',                 
  env: {
    NEXT_PUBLIC_BACKEND_URL:
      process.env.NEXT_PUBLIC_BACKEND_URL || "https://debate-mate.onrender.com/api"
  }
};
