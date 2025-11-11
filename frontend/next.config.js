/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: ['www.ahana.co.in'],
    unoptimized: true, // Disable image optimization for offline builds
  },
  // Disable SWC minify if causing issues in offline environments
  swcMinify: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/:path*`,
        // Exclude our internal API routes
        has: [
          {
            type: 'header',
            key: 'x-skip-rewrite',
            value: '1',
          },
        ],
      },
    ];
  },
}

module.exports = nextConfig 