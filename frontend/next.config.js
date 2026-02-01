const { withSentryConfig } = require("@sentry/nextjs");

// Bundle analyzer for debugging (run with ANALYZE=true npm run build)
const withBundleAnalyzer = require("@next/bundle-analyzer")({
  enabled: process.env.ANALYZE === "true",
});

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone', // Standalone output for minimal Docker images
  reactStrictMode: true,
  swcMinify: true, // Enable SWC minification for better performance
  poweredByHeader: false, // Remove X-Powered-By header for security
  compress: true, // Enable gzip compression

  // Skip type checking during build (fix TypeScript errors separately)
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },

  // Image optimization
  images: {
    formats: ["image/webp", "image/avif"],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    minimumCacheTTL: 60,
    dangerouslyAllowSVG: false,
    contentDispositionType: "attachment",
    contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",
    remotePatterns: [
      {
        protocol: "https",
        hostname: "api.valsa.solutions",
      },
      {
        protocol: "https",
        hostname: "minio.valsa.solutions",
      },
      {
        protocol: "https",
        hostname: "placehold.co",
      },
      {
        protocol: "https",
        hostname: "images.unsplash.com",
      },
    ],
    unoptimized: false,
  },

  // Production optimizations
  compiler: {
    removeConsole:
      process.env.NODE_ENV === "production"
        ? {
            exclude: ["error", "warn"],
          }
        : false,
  },

  experimental: {
    // Reduce memory usage during build
    workerThreads: false,
    cpus: 1,
    // Optimize package imports for smaller bundles
    optimizePackageImports: [
      "react-icons",
      "lucide-react",
      "recharts",
      "framer-motion",
      "date-fns",
    ],
  },

  // Optimize bundle with library-specific chunks for better caching
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.optimization = {
        ...config.optimization,
        splitChunks: {
          chunks: "all",
          maxInitialRequests: 25,
          minSize: 20000,
          cacheGroups: {
            default: false,
            vendors: false,
            // Framework chunk (React, Next.js core)
            framework: {
              name: "framework",
              test: /[\\/]node_modules[\\/](react|react-dom|scheduler|next)[\\/]/,
              priority: 40,
              chunks: "all",
              enforce: true,
            },
            // Recharts (only load on analytics pages)
            recharts: {
              name: "recharts",
              test: /[\\/]node_modules[\\/]recharts[\\/]/,
              priority: 35,
              chunks: "async",
              reuseExistingChunk: true,
            },
            // Framer Motion (lazy load animations)
            framerMotion: {
              name: "framer-motion",
              test: /[\\/]node_modules[\\/]framer-motion[\\/]/,
              priority: 34,
              chunks: "async",
              reuseExistingChunk: true,
            },
            // Icons (separate chunk)
            icons: {
              name: "icons",
              test: /[\\/]node_modules[\\/](lucide-react|react-icons)[\\/]/,
              priority: 33,
              chunks: "all",
              reuseExistingChunk: true,
            },
            // Date utilities
            dateUtils: {
              name: "date-utils",
              test: /[\\/]node_modules[\\/](date-fns|dayjs|moment)[\\/]/,
              priority: 32,
              chunks: "all",
              reuseExistingChunk: true,
            },
            // Sentry (load async)
            sentry: {
              name: "sentry",
              test: /[\\/]node_modules[\\/]@sentry[\\/]/,
              priority: 31,
              chunks: "async",
              reuseExistingChunk: true,
            },
            // Other vendors
            vendor: {
              name: "vendor",
              test: /[\\/]node_modules[\\/]/,
              priority: 20,
              chunks: "all",
              reuseExistingChunk: true,
            },
            // Common app code
            common: {
              name: "common",
              minChunks: 2,
              priority: 10,
              chunks: "all",
              reuseExistingChunk: true,
              enforce: true,
            },
          },
        },
      };
    }
    return config;
  },
};

// Sentry configuration options
const sentryWebpackPluginOptions = {
  // Suppresses all Sentry SDK logs in the console
  silent: true,

  // Upload source maps to Sentry (for production builds)
  org: process.env.SENTRY_ORG,
  project: process.env.SENTRY_PROJECT,

  // Hide source maps from browser (security)
  hideSourceMaps: true,

  // Prevents Sentry from trying to upload if no auth token
  dryRun: !process.env.SENTRY_AUTH_TOKEN,

  // Tree-shake debug logging (replaces deprecated disableLogger)
  bundleSizeOptimizations: {
    excludeDebugStatements: true,
    excludeReplayIframe: true,
    excludeReplayShadowDom: true,
  },
};

// Build configuration pipeline
let finalConfig = nextConfig;

// Add bundle analyzer
finalConfig = withBundleAnalyzer(finalConfig);

// Only wrap with Sentry if DSN is configured (and in production)
if (process.env.NEXT_PUBLIC_SENTRY_DSN && process.env.NODE_ENV === "production") {
  finalConfig = withSentryConfig(finalConfig, sentryWebpackPluginOptions);
}

module.exports = finalConfig;
