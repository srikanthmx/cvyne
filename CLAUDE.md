# AutoApply AI — Architecture Reference for AI Agents

> This file is the canonical source of truth for all AI agents working on this codebase.
> Read this fully before making any changes. Update it when architectural decisions change.

## Project Identity

**Name:** AutoApply AI (codename: cvyne)
**Purpose:** Automate job applications end-to-end — extract JD, personalize CV, generate PDF, autofill forms, submit.
**Stack:** Next.js 15 + FastAPI + browser-use + open-design + multi-LLM BYOK

---

## Monorepo Layout

```
cvyne/
├── apps/
│   ├── web/          # Next.js 15 (App Router) — user-facing frontend
│   └── api/          # FastAPI — orchestration, AI, agents
├── packages/
│   ├── shared-types/ # TypeScript types shared between web and API contracts
│   ├── ui/           # Shared shadcn-based component library
│   └── config/       # Shared ESLint, TS, Tailwind configs
├── infrastructure/
│   ├── docker/       # docker-compose for local dev + prod
│   └── scripts/      # seed, migrate, reset scripts
└── docs/
    ├── architecture/ # ADRs (Architecture Decision Records)
    └── agents/       # Work instructions for each agent (Codex, Antigravity, Kiro)
```

---

## Technology Decisions (non-negotiable)

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | Next.js 15 App Router | RSC, streaming, layouts |
| Styling | Tailwind CSS v4 | zero-config, CSS variables |
| Components | shadcn/ui | copy-owned, composable |
| State | Zustand + TanStack Query v5 | server/client split |
| Backend | FastAPI (Python 3.12+) | async, type-safe, AI ecosystem |
| Validation | Pydantic v2 | Python models + JSON schema |
| ORM | SQLAlchemy 2.0 async | type-safe queries |
| Migrations | Alembic | schema versioning |
| Queue | Celery + Redis | async job processing |
| Browser | browser-use | agentic form filling |
| Design | open-design | CV generation, PDF export |
| Auth | Clerk | JWT, OAuth, webhooks |
| Files | S3-compatible (MinIO local) | CV/resume storage |
| Observability | OpenTelemetry + Langfuse | LLM tracing, prompt metrics |

---

## AI Layer Architecture

### Prompt Registry (critical — read carefully)

All prompts live in `apps/api/prompts/`. **Never hardcode prompt strings in service files.**

```python
# Always use the registry
from prompts.registry import PromptRegistry

prompt = PromptRegistry.get("jd_extraction", version="latest")
rendered = prompt.render(job_url=url, raw_html=html)
```

Prompts support:
- **Versioning**: each prompt has a `version` string (semver-ish: `v1.0.0`)
- **Caching**: Anthropic cache_control blocks injected automatically for static system prompts
- **Variables**: Jinja2 templates with typed variable schemas
- **Evaluation hooks**: each prompt can declare eval metrics

### Multi-LLM Adapter

```
apps/api/core/llm.py
```

All LLM calls go through `LLMClient`. Never import `anthropic`, `openai`, or `google.generativeai` directly in service files.

```python
from core.llm import LLMClient

client = LLMClient.from_user_config(user_id)  # loads saved BYOK key
response = await client.complete(prompt, structured_output=ResumeSchema)
```

Supported providers: `anthropic`, `openai`, `gemini`, `ollama`

### Agent Protocol

Agents are stateless async classes in `apps/api/agents/`. Each agent:
- Receives a typed `Context` dataclass
- Returns a typed `Result` dataclass
- Emits structured events for observability
- Can be composed in `services/orchestrator.py`

---

## Data Flow (canonical)

```
1. User pastes job URL
2. POST /api/v1/jobs/extract
   → BrowserAgent.extract_jd(url) → JDSchema
3. POST /api/v1/resumes/personalize
   → OrchestratorService.personalize(resume_id, jd) → TailoredResumeSchema
   → ResumePersonalizer → ATS Optimizer → CoverLetterGenerator (optional)
4. POST /api/v1/cv/generate
   → DesignAgent.generate(tailored_resume, theme) → FileRef (S3)
5. POST /api/v1/applications/submit
   → BrowserAgent.autofill(job_url, cv_file, resume_data)
6. Worker updates ApplicationStatus → SSE stream to frontend
```

---

## Schema Contracts

### Resume (Python + TypeScript mirrors)
```json
{
  "id": "uuid",
  "name": "string",
  "email": "string",
  "phone": "string",
  "location": "string",
  "summary": "string",
  "skills": ["string"],
  "experience": [
    { "company": "string", "role": "string", "start": "date", "end": "date|null", "bullets": ["string"] }
  ],
  "education": [{ "institution": "string", "degree": "string", "year": "number" }],
  "projects": [{ "name": "string", "description": "string", "url": "string|null", "tech": ["string"] }],
  "certifications": [{ "name": "string", "issuer": "string", "date": "date" }]
}
```

TypeScript mirror lives in `packages/shared-types/src/resume.ts`.

---

## Environment Variables

```
# apps/api/.env
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://localhost:6379
S3_ENDPOINT=http://localhost:9000
S3_BUCKET=cvyne
ENCRYPTION_KEY=<32-byte-hex>          # for encrypting user API keys
LANGFUSE_SECRET_KEY=...
LANGFUSE_PUBLIC_KEY=...

# apps/web/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=...
CLERK_SECRET_KEY=...
```

---

## Coding Standards

### Python
- Python 3.12+, strict type annotations everywhere
- Pydantic v2 for all data models
- `async`/`await` throughout — no blocking I/O
- `ruff` for linting + formatting
- `pytest` with `anyio` for async tests

### TypeScript / Next.js
- `strict: true` in tsconfig
- Server Components by default; `"use client"` only at leaf nodes
- API calls via TanStack Query — no raw `fetch` in components
- `zod` for runtime validation at API boundaries
- `biome` for linting + formatting

### General
- Every public function has a type signature
- No `any` types
- Errors are typed (`Result<T, E>` pattern where possible)
- Feature flags via environment variables, not code comments

---

## Local Dev Setup

```bash
# Prerequisites: Docker, pnpm, Python 3.12, uv

# 1. Start infrastructure
docker compose -f infrastructure/docker/docker-compose.yml up -d

# 2. Install dependencies
pnpm install                           # frontend + packages
uv sync --project apps/api             # python backend

# 3. Database
cd apps/api && alembic upgrade head

# 4. Start services
pnpm dev                               # starts web + api via turbo
```

---

## What Makes This Architecturally Sound

1. **Prompt-as-Code**: Prompts are versioned, cached, and testable units — not strings scattered in files
2. **Agent Protocol**: Stateless typed agents composable into any orchestration (LangGraph, custom, future A2A)
3. **LLM Abstraction**: Provider swap with zero service changes — ready for new models
4. **Schema-First**: Shared types between frontend/backend eliminate drift
5. **Observability-Native**: Every LLM call traced, every prompt version tracked
6. **Queue-First**: All heavy operations are async jobs — UI gets SSE updates
7. **MCP-Ready**: API is designed to be exposed as MCP tools (see `apps/api/mcp_server.py`)

---

## Files Agents Must NOT Modify Without ADR

- `apps/api/core/llm.py` — LLM abstraction layer
- `apps/api/prompts/registry.py` — Prompt registry
- `packages/shared-types/src/*.ts` — Shared schema contracts
- `infrastructure/docker/docker-compose.yml` — Base infra

Create an ADR in `docs/architecture/` before changing these.
