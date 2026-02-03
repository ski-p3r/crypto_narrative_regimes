/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  env: {
    DB_URL: process.env.DB_URL,
  },
};

export default nextConfig;
