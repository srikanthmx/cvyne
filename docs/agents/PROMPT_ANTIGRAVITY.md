# Antigravity — Initial Work Prompt

> Copy everything below the `---` into Antigravity to kick off the frontend work.
> This is a self-contained brief. Antigravity should not need to ask follow-ups.

---

You are Antigravity, the frontend agent for the **AutoApply AI** monorepo at `/Users/srikanth/Documents/Projects/cvyne`.

**Read these files first, in this order, before writing any code:**
1. `CLAUDE.md` — architecture overview
2. `AGENTS.md` — your domain ownership and contracts (especially the SSE event format and file upload contract sections)
3. `docs/agents/ANTIGRAVITY.md` — your detailed work queue

## Your Mission

Build the user-facing experience for AutoApply AI. The backend (Codex + Kiro) gives you a typed API: paste a job URL → personalize a resume → generate a CV → autofill the application form. Your job is to make that pipeline feel fast, magical, and trustworthy.

## Coordination Notes

- **Backend exists.** Kiro and Codex have wired the API: `POST /api/v1/jobs/extract`, `POST /api/v1/resumes/`, `POST /api/v1/resumes/parse`, `POST /api/v1/applications/`, `GET /api/v1/applications/{id}/stream` (SSE), `POST /api/v1/settings/api-keys`. Hit `http://localhost:8000/docs` to see the live OpenAPI spec.
- **Auth is Clerk** (already configured in `app/layout.tsx`). The user's auth token is auto-attached to every API request via `lib/api.ts:onRequest`.
- **Types are auto-generated** from FastAPI's OpenAPI. Never hand-mirror types — run `pnpm --filter shared-types generate` after backend changes and import from `shared-types`.

## Deliverables (in strict order)

### P0 — Foundation

1. **Install dependencies and shadcn/ui:**
   ```bash
   pnpm install
   cd apps/web
   pnpm dlx shadcn@latest init     # use defaults; accept Tailwind v4 + base color "neutral"
   pnpm dlx shadcn@latest add button input textarea card badge progress toast dialog select label form skeleton sonner dropdown-menu
   ```
   Replace the placeholder `apps/web/components/ui/toaster.tsx` with the real shadcn `Toaster` (or `Sonner`).

2. **Generate the typed API client:**
   ```bash
   # In one terminal: start the backend
   cd apps/api && make dev
   # In another terminal: generate types
   pnpm --filter shared-types generate
   ```
   Verify `packages/shared-types/src/api.gen.ts` is now populated with real OpenAPI types. Commit it.

3. **Verify the auth + dashboard shell renders.** Set up Clerk credentials in `apps/web/.env.local` (test keys are fine), then `pnpm dev`. Confirm:
   - `/` redirects to `/login` when signed out, `/dashboard/jobs` when signed in
   - Sidebar shows 4 nav items + UserButton
   - All 4 dashboard routes exist (jobs, resumes, applications, settings) — empty pages are fine for now

### P1 — Core flow: paste → apply

4. **`apps/web/app/(dashboard)/resumes/page.tsx`** — resume management:
   - Empty state with two CTAs: "Upload existing resume" (PDF/DOCX) and "Build from scratch"
   - Upload flow: file input → `POST /api/v1/resumes/parse` → returns parsed `ResumeSchema` → render in editable form → save via `POST /api/v1/resumes/`
   - Form built with `react-hook-form` + `zod`. Validate against the same schema.
   - Mark one resume as `is_base: true`. Show a list of saved resumes below the editor.

5. **`apps/web/components/jobs/JobUrlInput.tsx`** — replace the stub:
   - Textarea accepts multiple URLs (one per line)
   - "Extract & Apply" button:
     - For each URL, calls `jobsApi.extract(url)` (already typed in `lib/api.ts`)
     - Optimistically adds a card to the queue with status "extracting"
     - Polls `GET /api/v1/jobs/{id}` every 2s until `status === "extracted"` or `"failed"`
     - On extracted, surfaces a "Generate CV & Apply" button that opens a theme picker dialog

6. **`apps/web/components/jobs/JobQueue.tsx`** — replace the stub:
   - Lists user's jobs (you'll need a `GET /api/v1/jobs/` list endpoint — if it doesn't exist yet, file a one-line note in `docs/architecture/` requesting it from Kiro and use a TanStack Query placeholder)
   - Each row shows: company logo (favicon trick: `https://www.google.com/s2/favicons?domain=...`), title, company, status badge, action button

7. **`apps/web/components/applications/ApplicationStatus.tsx`** — the magic moment:
   - Opens `EventSource` via `applicationsApi.streamStatus(id)`
   - Renders a stepper: "Extracting JD" → "Personalizing resume" → "Generating CV" → "Filling form" → "Submitted"
   - Live progress bar bound to `event.progress`
   - Terminal states:
     - `submitted` → green check + link to download CV
     - `failed` → red alert + retry button
     - `requires_human` → yellow callout: "CAPTCHA detected — open in browser to finish manually"
   - Critical: clean up the `EventSource` on unmount and on terminal status

### P2 — Settings & polish

8. **`apps/web/app/(dashboard)/settings/page.tsx`** — model + API key management:
   - Section "LLM Provider": Select dropdown (Anthropic / OpenAI / Gemini / Ollama)
   - Section "API Keys": For each provider, masked input with "Save" button → `POST /api/v1/settings/api-keys`
   - Section "Default CV Theme": radio group (ats / modern / creative / portfolio) with a small visual preview
   - Persist user choices to Zustand store + localStorage

9. **`apps/web/app/(dashboard)/applications/page.tsx`** — history view:
   - Table of past applications: date, company, role, status, CV download, actions
   - Filters by status
   - Empty state

10. **Polish pass:**
    - Add `loading.tsx` files to each route for streaming Suspense
    - Add `error.tsx` boundaries with retry buttons
    - Toast notifications on every mutation success/failure
    - Mobile responsive: sidebar collapses to bottom nav on `<md`

## Acceptance Criteria

You're done with P0–P2 when ALL of these pass:

- [ ] `pnpm install && pnpm --filter web build` succeeds with no TS errors
- [ ] `pnpm --filter web dev` starts cleanly; `http://localhost:3000` redirects appropriately based on auth state
- [ ] Uploading a resume PDF parses to a structured form (verify with a real PDF)
- [ ] Pasting a job URL persists and shows in the queue with a live status badge
- [ ] Submitting an application opens the SSE stream and the stepper advances through 4+ states
- [ ] Saving an API key in Settings round-trips: refresh, the masked key is still listed
- [ ] All API calls are type-safe — `pnpm --filter web type-check` passes with `noUncheckedIndexedAccess: true`
- [ ] No raw `fetch()` calls in components — only via `lib/api.ts` helpers consumed by hooks in `hooks/`
- [ ] Lighthouse score >85 on the dashboard pages (run in incognito)

## Hard Rules

- **Never** modify anything under `apps/api/` — Codex and Kiro's domain.
- **Never** modify `packages/shared-types/src/api.gen.ts` by hand — regenerate it.
- **Server Components by default.** Add `"use client"` only when the file uses hooks, event handlers, or browser APIs. Lift client boundaries as deep into the tree as possible.
- **No raw `fetch`** in components. Use the typed helpers in `lib/api.ts` consumed via TanStack Query hooks in `apps/web/hooks/`.
- **All API response types** imported from `shared-types`. No re-defining shapes inline.
- **All forms** use `react-hook-form` + `zod`. Validate before submit, never on submit only.
- **No inline styles.** Tailwind classes only.
- **Accessible:** every interactive element has an aria label or visible text label.
- **Cleanup:** `EventSource`, intervals, subscriptions all torn down on unmount.

## Important Patterns

### TanStack Query hook example
```ts
// hooks/useExtractJob.ts
"use client";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { jobsApi } from "@/lib/api";

export function useExtractJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (url: string) => jobsApi.extract(url),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["jobs"] }),
  });
}
```

### SSE consumption pattern
```ts
// hooks/useApplicationStream.ts
"use client";
import { useEffect, useState } from "react";
import { applicationsApi } from "@/lib/api";
import type { components } from "shared-types";

type StatusEvent = components["schemas"]["ApplicationStatusEvent"];

export function useApplicationStream(applicationId: string | null) {
  const [event, setEvent] = useState<StatusEvent | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!applicationId) return;
    const es = applicationsApi.streamStatus(applicationId);

    es.addEventListener("status_update", (e) => {
      setEvent(JSON.parse((e as MessageEvent).data));
    });
    es.addEventListener("done", () => {
      setDone(true);
      es.close();
    });
    es.onerror = () => es.close();

    return () => es.close();
  }, [applicationId]);

  return { event, done };
}
```

### Form pattern
```tsx
// All forms follow this shape — no exceptions
const schema = z.object({ email: z.string().email(), name: z.string().min(1) });
type FormData = z.infer<typeof schema>;

const form = useForm<FormData>({ resolver: zodResolver(schema) });
const mutation = useSaveResume();
const onSubmit = form.handleSubmit((data) => mutation.mutate(data));
```

## Reporting Back

When you're done with each priority block (P0, P1, P2), report:
1. Files created or modified (paths only)
2. Acceptance criteria from that block that now pass
3. Any backend gaps you hit (e.g. "needed `GET /api/v1/jobs/` list endpoint, filed note for Kiro")
4. Any UX decisions you made that diverge from the spec, and why
