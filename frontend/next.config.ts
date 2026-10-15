import type { NextConfig } from "next";

const isDev = process.env.NODE_ENV !== "production";
const devApiUrl = process.env.DEV_API_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  // Production build is a static export served by Netlify; /api/* is proxied to the backend
  // by Netlify (see netlify.toml). In dev, a rewrite mimics that proxy so cookies stay
  // same-origin. Rewrites are not allowed together with `output: "export"`.
  output: isDev ? undefined : "export",
  // Lets E2E run its own dev server next to the one used for development.
  distDir: process.env.NEXT_DIST_DIR ?? ".next",
  ...(isDev && {
    rewrites: async () => [{ source: "/api/:path*", destination: `${devApiUrl}/api/:path*` }],
  }),
  // The dev-tools badge would cover the bottom navigation on phones.
  devIndicators: false,
  turbopack: {
    // Pin the workspace root (a lockfile elsewhere on the machine would be picked up otherwise).
    root: import.meta.dirname,
    rules: {
      "*.css": { loaders: ["@tailwindcss/turbopack"], as: "*.css" },
    },
  },
};

export default nextConfig;
