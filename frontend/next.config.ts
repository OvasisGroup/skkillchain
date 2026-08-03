import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Pins the workspace root to this directory — without it, Next.js finds
  // an unrelated lockfile higher up the filesystem and warns about an
  // ambiguous root.
  turbopack: {
    root: path.resolve(__dirname),
  },
};

export default nextConfig;
