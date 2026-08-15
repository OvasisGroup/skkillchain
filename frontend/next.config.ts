import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Pins the workspace root to this directory — without it, Next.js finds
  // an unrelated lockfile higher up the filesystem and warns about an
  // ambiguous root.
  turbopack: {
    root: path.resolve(__dirname),
  },
  // Emits a self-contained .next/standalone server (just the files actually
  // needed at runtime, node_modules pruned to production deps) — frontend/
  // Dockerfile's runtime stage copies only that output rather than the full
  // node_modules tree, which is most of why the production image is small.
  output: "standalone",
  // Removes the "X-Powered-By: Next.js" response header — no functional
  // value to a legitimate client, just free reconnaissance for an attacker.
  poweredByHeader: false,
  // Course covers and profile avatars are user-uploaded originals served
  // as-is by nginx (see infra/nginx/skillchain.conf's /media/ location) —
  // multi-megabyte JPEGs/PNGs straight from a phone camera, not
  // pre-resized. Without this, next/image refuses to optimize a remote
  // host it doesn't know about, which is why these were plain <img> tags
  // shipping full-resolution originals into a ~400px card.
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "api.skillchain.space", pathname: "/media/**" },
      { protocol: "http", hostname: "localhost", port: "8000", pathname: "/media/**" },
    ],
  },
  // Next.js sends none of these by default. The API (Django's
  // SecurityMiddleware) already sets the equivalents, but the frontend
  // origin (www.skillchain.space) was serving pages with no HSTS/framing/
  // sniffing protection at all. No Content-Security-Policy here yet — a
  // wrong CSP silently breaks Google Sign-In / API calls / images rather
  // than failing loudly, so it needs deliberate source enumeration and
  // testing rather than a guessed policy shipped alongside unrelated fixes.
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "Strict-Transport-Security",
            value: "max-age=31536000; includeSubDomains; preload",
          },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "same-origin" },
        ],
      },
    ];
  },
};

export default nextConfig;
