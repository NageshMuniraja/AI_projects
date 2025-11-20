/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  transpilePackages: ['@ai-agent-platform/shared-types', '@ai-agent-platform/utils'],
  images: {
    domains: ['img.clerk.com'],
  },
  experimental: {
    serverActions: true,
  },
}

module.exports = nextConfig
