# Antigravity Work Instructions — Frontend

> Read CLAUDE.md and AGENTS.md first. This file is Antigravity-specific detail.

## Your Domain

You own everything the user sees and interacts with. The product lives or dies on UX quality.

## Starting Point (what exists)

Scaffold only:
- `apps/web/app/layout.tsx` — root layout with Clerk + QueryProvider
- `apps/web/app/page.tsx` — redirect to dashboard or login
- `apps/web/app/(dashboard)/layout.tsx` — dashboard shell (Sidebar not yet built)
- `apps/web/app/(dashboard)/jobs/page.tsx` — page stub
- `apps/web/lib/api.ts` — typed API client
- `apps/web/lib/query-provider.tsx` — TanStack Query setup
- `packages/shared-types/src/` — all types ready to import

## First Thing to Build

**Install deps and set up shadcn:**
```bash
cd apps/web
pnpm dlx shadcn@latest init
pnpm dlx shadcn@latest add button input card badge progress toast dialog select
```

Then build `components/dashboard/Sidebar.tsx` — the shell everything depends on.

## Component Priorities

### 1. Sidebar (unblocks everything)
```tsx
// Nav items:
// - /dashboard/jobs (Briefcase icon)
// - /dashboard/resumes (FileText icon)
// - /dashboard/applications (Send icon)
// - /dashboard/settings (Settings icon)
// Bottom: UserButton from Clerk
```

### 2. JobUrlInput (core interaction)
```tsx
// - Textarea for pasting multiple URLs (one per line)
// - "Extract All" button
// - Calls jobsApi.extract() for each URL
// - Shows extraction progress inline
// - Persists to TanStack Query cache
```

### 3. ApplicationStatus (real-time magic)
```tsx
// - Consumes EventSource from applicationsApi.streamStatus(id)
// - Progress bar tied to event.progress
// - Step labels: "Extracting JD" → "Personalizing" → "Generating CV" → "Submitting"
// - Terminal states: success/failed/requires_human with appropriate UI
```

## State Architecture

```
Global (Zustand):
  - selectedModel: LLMProvider
  - selectedTheme: CVTheme

Server (TanStack Query):
  - useJobs() — job list
  - useResume(id) — single resume
  - useApplicationStatus(id) — polling fallback if SSE fails

Form (react-hook-form + zod):
  - ResumeEditor — all resume fields validated before save
  - ApiKeyForm — provider + key validation
```

## Hooks to Build

```
hooks/
├── useJobs.ts           → GET /api/v1/jobs
├── useSubmitJob.ts      → POST /api/v1/jobs/extract (mutation)
├── useResume.ts         → GET /api/v1/resumes/:id
├── useApplicationStream.ts  → SSE EventSource
└── useSettings.ts       → GET/POST /api/v1/settings/api-keys
```

## Design Principles

- **Optimistic UI**: job cards appear instantly when URL pasted, update when extraction completes
- **Empty states**: every list page has a helpful empty state, not a blank screen
- **Loading skeletons**: use `Skeleton` components — not spinners for content areas
- **Error recovery**: failed applications show a "Retry" button
- **Requires Human state**: clear callout with link to open the form manually in browser

## Routing

```
/                     → redirect (handled)
/login                → Clerk hosted UI or custom
/dashboard/jobs       → main entry point
/dashboard/resumes    → upload + manage base resumes
/dashboard/applications → history + status
/dashboard/settings   → model selection + API keys
```

## TypeScript Rules

- All API response types from `shared-types` package: `import type { JobResponse } from "shared-types"`
- No `any`, no `as` casts without `// eslint-disable` comment explaining why
- All `useQuery` calls have explicit `queryKey` and `queryFn` types
