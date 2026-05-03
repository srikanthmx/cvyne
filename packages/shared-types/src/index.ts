/**
 * Shared types between FastAPI and Next.js.
 *
 * Two layers:
 * 1. ./api.gen.ts — auto-generated from FastAPI's /openapi.json
 *    Run `pnpm --filter shared-types generate` to refresh after backend changes.
 * 2. ./resume.ts, ./job.ts — hand-written convenience aliases that re-export
 *    the generated types with friendlier names. Antigravity imports from here.
 */

export * from "./resume";
export * from "./job";

// Re-export generated types under `Api` namespace
export type { paths, components } from "./api.gen";
