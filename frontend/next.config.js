/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    // Security: Remove X-Powered-By header
    poweredByHeader: false,

    // React Compiler disabled - requires babel-plugin-react-compiler
    // Security patches are in the Next.js/React runtime, not the compiler
    // reactCompiler: true,

    // Turbopack configuration (Next.js 16 default bundler)
    // Empty config silences the webpack migration warning
    turbopack: {},

    // Security hardening for Server Actions
    experimental: {
        serverActions: {
            bodySizeLimit: '1mb', // Limit server action payload size
        },
    },

    images: {
        remotePatterns: [
            {
                protocol: 'https',
                hostname: 'raw.githubusercontent.com',
            },
            {
                protocol: 'https',
                hostname: 'arweave.net',
            },
            {
                protocol: 'https',
                hostname: 'www.arweave.net',
            },
            {
                protocol: 'https',
                hostname: 'shdw-drive.genesysgo.net',
            },
        ],
    },

    // Security headers
    async headers() {
        return [
            {
                source: '/(.*)',
                headers: [
                    {
                        key: 'X-Content-Type-Options',
                        value: 'nosniff',
                    },
                    {
                        key: 'X-Frame-Options',
                        value: 'DENY',
                    },
                    {
                        key: 'X-XSS-Protection',
                        value: '1; mode=block',
                    },
                    {
                        key: 'Referrer-Policy',
                        value: 'strict-origin-when-cross-origin',
                    },
                    {
                        key: 'Permissions-Policy',
                        value: 'camera=(), microphone=(), geolocation=()',
                    },
                    {
                        key: 'Content-Security-Policy',
                        value: "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https: blob:; connect-src 'self' https: wss:; frame-ancestors 'none';",
                    },
                ],
            },
        ];
    },
};

module.exports = nextConfig;

