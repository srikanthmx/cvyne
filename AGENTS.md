# Agent Work Directions — AutoApply AI

> Read CLAUDE.md first. This file assigns ownership and work scope per agent.
> Agents should not cross into each other's domains without coordination.

---

## Agent Roster

| Agent | Domain | Primary Files |
|-------|--------|--------------|
| **Codex** | Backend AI layer, agents, prompts, orchestration | `apps/api/` |
| **Antigravity** | Frontend, UX, design system, real-time UI | `apps/web/`, `packages/ui/` |
| **Kiro** | Infrastructure, workers, DevOps, data layer | `infrastructure/`, `apps/api/db/`, `apps/api/workers/` |

---

## Codex — AI Backend Agent

### Ownership
- `apps/api/agents/` — browser_agent, design_agent, llm_agent
- `apps/api/services/` — orchestrator, jd_extractor, resume_personalizer, ats_optimizer, cover_letter, autofill
- `apps/api/prompts/` — registry, all templates
- `apps/api/core/llm.py` — multi-LLM adapter
- `apps/api/routers/` — FastAPI route handlers
- `apps/api/models/` — Pydantic schemas

### Work Queue (priority order)

**P0 — Foundation (do first)**
1. `apps/api/core/llm.py` — Implement `LLMClient` with Anthropic, OpenAI, Gemini, Ollama adapters. Use prompt caching (cache_control) for Anthropic by default.
2. `apps/api/prompts/registry.py` — Implement `PromptRegistry` with version resolution, Jinja2 rendering, cache_control injection.
3. `apps/api/models/resume.py` + `job.py` + `application.py` — Full Pydantic v2 models matching schema in CLAUDE.md.

**P1 — Core Services**
4. `apps/api/agents/browser_agent.py` — Wraps [browser-use](https://github.com/browser-use/browser-use) (Python lib). Use bundled `ChatAnthropic`/`ChatOpenAI`/`ChatGoogle`/`ChatBrowserUse` — no LangChain. Methods: `extract_jd(url)`, `autofill_form(url, data, cv_path)`. CAPTCHA → `status: requires_human`.
5. `apps/api/agents/design_agent.py` — HTTP client for [open-design](https://github.com/nexu-io/open-design) **sidecar daemon** (not a Python lib — runs separately at `OPEN_DESIGN_URL`). Methods: `generate_cv(resume, theme)` → S3 FileRef. Themes: `ats`, `modern`, `creative`, `portfolio` mapped to design system slugs.
6. `apps/api/services/orchestrator.py` — Compose agents into the end-to-end flow. Use async task graph, not sequential blocking calls.

**P2 — Intelligence Layer**
7. `apps/api/services/jd_extractor.py` — Parse JD HTML into structured `JobSchema`.
8. `apps/api/services/resume_personalizer.py` — Score bullets vs JD, rewrite with keyword injection. Never fabricate experience.
9. `apps/api/services/ats_optimizer.py` — Keyword density, section normalization.
10. `apps/api/services/cover_letter.py` — Generate from JD + resume, optional per-application toggle.

**P3 — API Layer**
11. `apps/api/routers/jobs.py` — `POST /v1/jobs/extract`, `GET /v1/jobs/{id}`
12. `apps/api/routers/resumes.py` — CRUD for resumes + `POST /v1/resumes/{id}/personalize`
13. `apps/api/routers/applications.py` — `POST /v1/applications/submit`, `GET /v1/applications/{id}/stream` (SSE)
14. `apps/api/routers/settings.py` — Save encrypted API keys per user

### Rules Codex Must Follow
- All LLM calls through `LLMClient`, never direct SDK imports in services
- All prompts through `PromptRegistry`, never inline strings
- Return typed `Result` objects, raise typed exceptions
- Every agent method is independently testable (no side effects in constructors)
- Anthropic calls must use `cache_control: {"type": "ephemeral"}` on system prompts >1024 tokens

### Key Interfaces to Implement

```python
# core/llm.py
class LLMClient:
    @classmethod
    def from_user_config(cls, user_id: str) -> "LLMClient": ...
    async def complete(self, prompt: RenderedPrompt, structured_output: type[T] | None = None) -> T | str: ...
    async def stream(self, prompt: RenderedPrompt) -> AsyncIterator[str]: ...

# prompts/registry.py
class PromptRegistry:
    @classmethod
    def get(cls, name: str, version: str = "latest") -> Prompt: ...

class Prompt:
    def render(self, **kwargs) -> RenderedPrompt: ...

# agents/browser_agent.py
class BrowserAgent:
    async def extract_jd(self, url: str) -> JDSchema: ...
    async def autofill_form(self, url: str, data: ResumeSchema, cv_path: str) -> ApplicationResult: ...

# agents/design_agent.py
class DesignAgent:
    async def generate_cv(self, resume: TailoredResumeSchema, theme: CVTheme) -> FileRef: ...
```

---

## Antigravity — Frontend Agent

### Ownership
- `apps/web/` — entire Next.js app
- `packages/ui/src/` — shared component library
- `packages/shared-types/src/` — TypeScript type definitions (coordinate with Codex on schema)

### Work Queue (priority order)

**P0 — Foundation**
1. `apps/web/` — Initialize Next.js 15, Tailwind v4, shadcn/ui, Clerk auth, TanStack Query.
2. `packages/shared-types/src/` — Mirror all Pydantic models as TypeScript interfaces.
3. `apps/web/lib/api.ts` — Type-safe API client using `ky` or `axios` with base URL from env.

**P1 — Core Pages**
4. `apps/web/app/(auth)/` — Login/signup via Clerk hosted UI redirect.
5. `apps/web/app/(dashboard)/layout.tsx` — Dashboard shell: sidebar nav, user menu, toast provider.
6. `apps/web/app/(dashboard)/resumes/` — Resume upload (JSON/PDF parse), profile editor form.
7. `apps/web/app/(dashboard)/jobs/` — URL paste input, bulk job queue list, status badges.
8. `apps/web/app/(dashboard)/applications/` — Application history, status timeline, download CV.

**P2 — Intelligence UX**
9. Resume diff viewer — show what changed between base and tailored resume.
10. Real-time application status — SSE stream from `GET /v1/applications/{id}/stream`.
11. Model selector + API key entry in Settings (masked input, test connection button).
12. CV theme picker with live preview thumbnails.

**P3 — Polish**
13. Optimistic UI for job submission.
14. Dashboard analytics: applied count, success rate, pending.
15. Mobile responsive layout.

### Rules Antigravity Must Follow
- Server Components by default. Add `"use client"` only when hooks or events needed.
- No raw `fetch` in components — use TanStack Query hooks in `hooks/` directory.
- All API response types imported from `packages/shared-types`.
- Form validation with `react-hook-form` + `zod`.
- No inline styles — Tailwind classes only.
- Accessible: all interactive elements have aria labels.

### Key Components to Build

```
components/
├── resume/
│   ├── ResumeEditor.tsx       # structured JSON form editor
│   ├── ResumeDiff.tsx         # base vs tailored diff
│   └── ResumeUploader.tsx     # drag-drop + parse
├── jobs/
│   ├── JobUrlInput.tsx        # paste + bulk add
│   ├── JobCard.tsx            # JD summary card
│   └── JobQueue.tsx           # list with status
├── cv/
│   ├── ThemePicker.tsx        # visual theme selector
│   └── CVPreview.tsx          # iframe or image preview
├── applications/
│   ├── ApplicationStatus.tsx  # SSE-powered live status
│   └── ApplicationTimeline.tsx
└── dashboard/
    ├── Sidebar.tsx
    ├── StatsBar.tsx
    └── ModelSelector.tsx
```

---

## Kiro — Infrastructure Agent

### Ownership
- `infrastructure/` — all Docker, compose files
- `apps/api/db/` — migrations, schema, seed data
- `apps/api/workers/` — Celery app, task definitions
- `apps/api/core/config.py` — settings, env loading
- `infrastructure/scripts/` — dev utility scripts

### Work Queue (priority order)

**P0 — Foundation**
1. `infrastructure/docker/docker-compose.yml` — PostgreSQL 16, Redis 7, MinIO, Langfuse (optional profile).
2. `apps/api/core/config.py` — Pydantic Settings v2, load from `.env`, validate all required vars.
3. `apps/api/db/base.py` — SQLAlchemy 2.0 async engine + session factory.

**P1 — Schema + Migrations**
4. `apps/api/db/models.py` — SQLAlchemy ORM models: User, Resume, Job, Application, ApiKey.
5. Alembic setup + initial migration `001_initial_schema.py`.
6. `infrastructure/scripts/seed.py` — Sample resume + test job for dev.

**P2 — Worker Infrastructure**
7. `apps/api/workers/celery_app.py` — Celery with Redis broker + result backend.
8. `apps/api/workers/tasks.py` — Async tasks: `process_job_application`, `generate_cv_task`, `extract_jd_task`.
9. Beat schedule for retry of failed applications (exponential backoff, max 3 attempts).

**P3 — Observability**
10. OpenTelemetry instrumentation for FastAPI + SQLAlchemy.
11. Langfuse tracing middleware.
12. Health check endpoints: `GET /health`, `GET /health/deep`.

### Rules Kiro Must Follow
- All secrets via env vars — never hardcoded.
- API keys stored encrypted (AES-256-GCM) in DB, encryption key from env.
- Database migrations are additive — never drop columns, use nullable + backfill pattern.
- Celery tasks are idempotent — safe to retry.
- Docker services have health checks and restart policies.

### Database Schema (canonical)

```sql
-- users managed by Clerk, synced via webhook
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clerk_id TEXT UNIQUE NOT NULL,
  email TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE resumes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  name TEXT NOT NULL,
  data JSONB NOT NULL,  -- ResumeSchema JSON
  is_base BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  url TEXT NOT NULL,
  raw_jd JSONB,          -- extracted JD
  status TEXT NOT NULL DEFAULT 'pending',  -- pending | extracted | failed
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE applications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  job_id UUID REFERENCES jobs(id),
  resume_id UUID REFERENCES resumes(id),
  tailored_resume JSONB,
  cv_file_key TEXT,      -- S3 key
  theme TEXT,
  status TEXT DEFAULT 'queued', -- queued | processing | submitted | failed | requires_human
  error TEXT,
  attempts INTEGER DEFAULT 0,
  submitted_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  provider TEXT NOT NULL,  -- anthropic | openai | gemini | ollama
  encrypted_key TEXT NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Cross-Agent Contracts

### How to propose schema changes
1. Open a discussion in `docs/architecture/` as an ADR draft.
2. Both affected agents review.
3. Update `packages/shared-types/` and `apps/api/models/` together.

### SSE Event Format (Codex implements, Antigravity consumes)
```json
{ "event": "status_update", "data": { "application_id": "uuid", "status": "processing", "step": "jd_extraction", "progress": 20 } }
{ "event": "status_update", "data": { "application_id": "uuid", "status": "submitted", "step": "done", "progress": 100 } }
{ "event": "error", "data": { "application_id": "uuid", "code": "captcha_required", "message": "..." } }
```

### File Upload Contract (Kiro implements, Codex writes, Antigravity reads)
```
S3 key pattern: {user_id}/cvs/{application_id}/{theme}.pdf
Presigned URL TTL: 1 hour
Max file size: 10MB
```
