/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone', // Required for Docker
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8005',
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8005',
    NEXT_PUBLIC_TELEMETRY_SIM: '0',  // DISABLED - Real data only
    NEXT_PUBLIC_COCKPIT_RENDERER: process.env.NEXT_PUBLIC_COCKPIT_RENDERER || 'v2',
  },
}

module.exports = nextConfig
