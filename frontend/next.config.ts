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
};

export default nextConfig;
