/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  images: {
    domains: ['dalleprodaue.blob.core.windows.net'],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'dalleprodaue.blob.core.windows.net',
        port: '',
        pathname: '/private/images/**',
      },
    ],
  },
}

module.exports = nextConfig
