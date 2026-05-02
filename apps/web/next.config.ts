import type { NextConfig } from "next";

const config: NextConfig = {
  experimental: {
    ppr: true,           // Partial Prerendering
    reactCompiler: true, // React Compiler (auto-memoization)
  },
  logging: {
    fetches: { fullUrl: true },
  },
};

export default config;
