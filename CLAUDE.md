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

**Philosophy:** lean on open-source maximally. Every row below is a battle-tested OSS choice.

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | Next.js 15 App Router | RSC, streaming, layouts |
| Styling | Tailwind CSS v4 | zero-config, CSS variables |
| Components | shadcn/ui | copy-owned, composable |
| State | Zustand + TanStack Query v5 | server/client split |
| API client | [openapi-fetch](https://openapi-ts.dev/) | type-safe paths from FastAPI's OpenAPI |
| Backend | FastAPI (Python 3.12+) | async, type-safe, AI ecosystem |
| Validation | Pydantic v2 | Python models + JSON schema |
| ORM | SQLAlchemy 2.0 async | type-safe queries |
| Migrations | Alembic | schema versioning |
| Queue | Celery + Redis + [Flower](https://flower.readthedocs.io/) | async jobs + monitoring UI |
| **LLM router** | [**litellm**](https://github.com/BerriAI/litellm) | unified API for 100+ providers, fallback, cost tracking, caching |
| **Structured output** | [**instructor**](https://github.com/instructor-ai/instructor) | Pydantic models from any LLM |
| Browser | [browser-use](https://github.com/browser-use/browser-use) | agentic form filling (Python lib) |
| Web scraping | [crawl4ai](https://github.com/unclecode/crawl4ai) | fast LLM-friendly scraping (JD fast-path) |
| Resume parsing | [pymupdf4llm](https://github.com/pymupdf/RAG) | PDF → markdown for upload flow |
| Design | [open-design](https://github.com/nexu-io/open-design) | CV artifact generation (TS sidecar daemon) |
| PDF rendering | [weasyprint](https://weasyprint.org/) | HTML → PDF fallback |
| Auth | Clerk (TODO: swap to better-auth for OSS) | JWT, OAuth, webhooks |
| Files | MinIO (S3-compatible) | local + prod object storage |
| Observability | [Langfuse](https://github.com/langfuse/langfuse) | wired as litellm callback — every LLM call traced automatically |

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

### Multi-LLM Adapter (litellm-backed)

```
apps/api/core/llm.py  (~150 lines wrapping litellm + instructor)
```

We do not write provider-specific code. `litellm` handles all 100+ providers via model strings (`anthropic/claude-sonnet-4-6`, `openai/gpt-4o`, etc.) and gives us:
- Automatic fallback chains on rate-limit/outage
- Per-call cost tracking (`response.cost`)
- Retry with exponential backoff
- Anthropic prompt caching (we inject `cache_control` for system prompts >1024 tokens)
- Langfuse callback wiring (every call auto-traced)
- Semantic response cache

`instructor` wraps litellm to give us Pydantic-typed responses from any provider.

```python
from core.llm import LLMClient

client = await LLMClient.from_user_config(user_id)  # decrypts saved BYOK key
resume = await client.complete(prompt, structured_output=TailoredResumeSchema)
# Pydantic instance, validated, ready to use
```

Supported providers: `anthropic`, `openai`, `gemini`, `ollama` (and via litellm: bedrock, azure, mistral, groq, together, openrouter, vertex, cohere — all free with no code changes).

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

---

## Open-Source Integrations (read these before changing the integration code)

### browser-use (Python library)
- **Repo:** https://github.com/browser-use/browser-use
- **Install:** `uv add browser-use && uv sync` then `uv run playwright install chromium`
- **LLM clients:** Use **only** browser-use's bundled clients — `ChatBrowserUse`, `ChatAnthropic`, `ChatOpenAI`, `ChatGoogle`. Do NOT introduce LangChain wrappers.
- **Lives in:** `apps/api/agents/browser_agent.py`

### open-design (TypeScript sidecar daemon)
- **Repo:** https://github.com/nexu-io/open-design
- **Not a Python library** — it's an Express + SQLite daemon (Node 24, pnpm 10.33).
- **Run locally:** `docker compose -f infrastructure/docker/docker-compose.yml --profile full up -d` (builds from GitHub) — OR clone repo and `pnpm tools-dev run web`.
- **We talk to it via REST/SSE** at `OPEN_DESIGN_URL` (default `http://localhost:4477`):
  - `POST /api/chat` (SSE) — agent CLI produces `<artifact>...</artifact>` HTML
  - `POST /api/artifacts/save` — store artifact
  - `GET /api/design-systems` — list available themes (DESIGN.md tokens)
  - `POST /api/proxy/stream` — BYOK OpenAI-compatible passthrough
- **Lives in:** `apps/api/agents/design_agent.py` (HTTP client, not lib import)
- **Theme mapping:** `THEME_TO_DESIGN_SYSTEM` in `design_agent.py` — verify slugs against `GET /api/design-systems` on first run.

---

## Files Agents Must NOT Modify Without ADR

- `apps/api/core/llm.py` — LLM abstraction layer
- `apps/api/prompts/registry.py` — Prompt registry
- `packages/shared-types/src/*.ts` — Shared schema contracts
- `infrastructure/docker/docker-compose.yml` — Base infra

Create an ADR in `docs/architecture/` before changing these.
