# Getting Started — AutoApply AI

A complete guide to running the project from a fresh clone. Skip ahead if you already have a section's prerequisites.

> **TL;DR for the impatient:**
> ```bash
> git clone <repo> && cd cvyne
> ./run.sh --setup          # installs deps + runs migrations (first time only)
> # then edit apps/api/.env and apps/web/.env.local
> ./run.sh                  # starts everything
> ```
> Open http://localhost:3000.

---

## 1. Prerequisites

Install these first. Versions matter — older versions will break.

| Tool | Min version | Install |
|------|-------------|---------|
| **Docker** | 24+ | https://www.docker.com/products/docker-desktop/ — start Docker Desktop before running anything |
| **Node.js** | 20+ | macOS: `brew install node`  •  Linux: https://nodejs.org/  •  Windows: https://nodejs.org/ |
| **pnpm** | 9+ | `npm install -g pnpm` |
| **Python** | 3.12+ | macOS: `brew install python@3.12`  •  Ubuntu: `sudo apt install python3.12`  •  Windows: https://www.python.org/downloads/ |
| **uv** (Python pkg mgr) | 0.5+ | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **git** | any | usually preinstalled |

Verify:
```bash
docker --version    # >= 24
node --version      # >= v20
pnpm --version      # >= 9
python3 --version   # >= 3.12
uv --version        # >= 0.5
```

> **Windows users:** use WSL2 (Ubuntu). Native Windows works for the frontend but Playwright + Celery on native Windows is painful.

---

## 2. Clone & first-run setup

```bash
git clone <your-repo-url> cvyne
cd cvyne

# One-time setup: installs all JS + Python deps, Playwright browser, runs DB migrations
./run.sh --setup
```

This will take **5–10 minutes** the first time (Playwright Chromium download is ~250 MB, Python deps include litellm and weasyprint).

If it bombs partway through, fix the error and rerun — `--setup` is idempotent.

---

## 3. Environment variables

You need two `.env` files. The runner will offer to scaffold the backend one for you.

### 3.1 Backend — `apps/api/.env`

```bash
cp .env.example apps/api/.env
```

Then fill in the keys below. **The runner auto-generates `ENCRYPTION_KEY` and `SECRET_KEY` if you let it.**

| Variable | Required? | Where to get it |
|----------|-----------|-----------------|
| `DATABASE_URL` | yes | leave default — Docker provides it |
| `REDIS_URL` | yes | leave default |
| `S3_*` | yes | leave defaults — MinIO is local |
| `ENCRYPTION_KEY` | yes | run `python3 -c "import secrets; print(secrets.token_hex(32))"` (or let `./run.sh --setup` generate it) |
| `SECRET_KEY` | yes | run `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `CLERK_SECRET_KEY` | yes | https://dashboard.clerk.com → **API Keys** → "Secret keys" — starts with `sk_test_` |
| `CLERK_WEBHOOK_SECRET` | optional | Clerk dashboard → **Webhooks** → create one pointing to `http://localhost:8000/api/webhooks/clerk` |
| `OPEN_DESIGN_URL` | yes | leave default `http://localhost:4477` (Docker sidecar) |
| `LANGFUSE_SECRET_KEY` | optional | https://cloud.langfuse.com → create project → settings → API keys (or self-host: https://github.com/langfuse/langfuse) |
| `LANGFUSE_PUBLIC_KEY` | optional | same place |

### 3.2 Frontend — `apps/web/.env.local`

Create it (it's gitignored):
```bash
cat > apps/web/.env.local <<EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_paste_yours_here
CLERK_SECRET_KEY=sk_test_paste_yours_here
EOF
```

Get Clerk keys at https://dashboard.clerk.com → **API Keys**. The publishable key starts with `pk_test_`, the secret starts with `sk_test_`.

> **Don't have a Clerk account?** Sign up free at https://clerk.com — takes 30 seconds. The free tier is generous (10K MAU).

### 3.3 LLM API keys (per-user, set in the app — NOT in env)

These are entered by each user in Settings → API Keys (encrypted at rest). For local testing, you can put one in your env to use `LLMClient.from_env()`:

| Provider | Get a key | Pricing |
|----------|-----------|---------|
| **Anthropic** | https://console.anthropic.com/settings/keys | https://www.anthropic.com/pricing |
| **OpenAI** | https://platform.openai.com/api-keys | https://openai.com/pricing |
| **Google Gemini** | https://aistudio.google.com/apikey | Free tier available |
| **Ollama** (local) | install via https://ollama.com — no key needed | Free, runs on your machine |

For backend smoke tests:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

---

## 4. Run the project

```bash
./run.sh
```

This starts everything in one terminal with prefixed, color-coded logs:

| Service | URL | What it is |
|---------|-----|-----------|
| Frontend | http://localhost:3000 | Next.js app |
| API | http://localhost:8000 | FastAPI |
| API docs | http://localhost:8000/docs | Interactive OpenAPI |
| Flower | http://localhost:5555 | Celery task dashboard |
| MinIO | http://localhost:9001 | Object storage console (login: `minioadmin` / `minioadmin`) |
| open-design | http://localhost:4477 | CV generation daemon |

Press **Ctrl+C** to stop the app processes. Docker services stay running. Use `./run.sh --stop` to tear down everything.

### Runner options

```bash
./run.sh                    # everything
./run.sh --no-design        # skip open-design (saves ~2GB RAM, uses fallback PDF)
./run.sh --no-beat          # skip Celery beat (no scheduled retry of failed apps)
./run.sh --infra-only       # just docker services, don't start app processes
./run.sh --stop             # tear down all docker services
./run.sh --setup            # reinstall deps + run migrations (idempotent)
```

---

## 5. Verify it works

After `./run.sh` is up, in another terminal:

```bash
# Health check
curl http://localhost:8000/health/deep
# Expect: {"status":"ok","db":"ok","redis":"ok"}

# Open the app
open http://localhost:3000              # macOS
xdg-open http://localhost:3000          # Linux
start http://localhost:3000             # Windows
```

End-to-end smoke test:
1. Sign in (Clerk hosted UI)
2. Go to **Settings → API Keys**, paste an Anthropic key, save
3. Go to **Resumes**, upload a PDF resume → review parsed structure → save as base
4. Go to **Jobs**, paste a job URL (try a Lever or Greenhouse one for the fast path)
5. Click **Generate CV & Apply** → watch the SSE stream advance through the steps

If any step fails, check the **Troubleshooting** section.

---

## 6. Daily workflow

```bash
./run.sh                  # morning
# work…
# Ctrl+C                  # evening (leaves docker up)

# Next morning, just:
./run.sh

# Reset everything:
./run.sh --stop
docker volume rm $(docker volume ls -q | grep cvyne)   # nukes data
./run.sh --setup
```

After backend schema changes:
```bash
# Codex/Kiro change Pydantic models → regenerate frontend types
pnpm --filter shared-types generate
```

After Python dep changes:
```bash
cd apps/api && uv sync
```

---

## 7. Project layout (where to look when something breaks)

```
cvyne/
├── run.sh                         ← single entrypoint (this guide)
├── apps/
│   ├── api/                       ← FastAPI backend (Python)
│   │   ├── main.py
│   │   ├── core/                  ← config, db, llm, security, telemetry
│   │   ├── routers/               ← HTTP endpoints
│   │   ├── services/              ← business logic
│   │   ├── agents/                ← browser-use, open-design wrappers
│   │   ├── prompts/               ← versioned LLM prompts
│   │   ├── workers/               ← Celery tasks
│   │   └── db/models.py           ← SQLAlchemy ORM
│   └── web/                       ← Next.js 15 frontend (TypeScript)
│       ├── app/                   ← routes
│       ├── components/            ← UI components
│       ├── hooks/                 ← TanStack Query hooks
│       └── lib/api.ts             ← typed API client (auto-generated from OpenAPI)
├── packages/shared-types/         ← TS types auto-generated from FastAPI
├── infrastructure/docker/         ← docker-compose.yml
└── docs/
    ├── architecture/              ← ADRs (decisions)
    └── agents/                    ← Codex / Kiro / Antigravity work directions
```

---

## 8. Troubleshooting

### Docker

| Problem | Fix |
|---------|-----|
| `Cannot connect to the Docker daemon` | Start Docker Desktop |
| Port `5432` / `6379` / `9000` already in use | `lsof -i :<port>` then kill, or change ports in `docker-compose.yml` |
| `docker compose --profile full up` is slow first time | Normal — open-design is built from source. Subsequent runs use the cached image. |

### Python / API

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` after pulling new code | `cd apps/api && uv sync` |
| Alembic migration fails | DB likely not running — `./run.sh --infra-only` then retry |
| `playwright._impl._api_types.Error: Executable doesn't exist` | `cd apps/api && uv run playwright install chromium` |
| `weasyprint` errors about pango/cairo on Linux | `sudo apt install libpango-1.0-0 libpangoft2-1.0-0` |
| Langfuse callback errors fill the logs | Either set `LANGFUSE_*` keys or leave them empty (telemetry is best-effort) |

### Frontend

| Problem | Fix |
|---------|-----|
| `Module not found: shared-types` | `pnpm install` from repo root |
| Type errors after backend change | `pnpm --filter shared-types generate` (API must be running) |
| Clerk redirect loops | Verify `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` and `CLERK_SECRET_KEY` are both set in `apps/web/.env.local` |
| `TypeError: Failed to fetch` on API calls | API not running — check `[api]` lines in runner log |

### LLM / agents

| Problem | Fix |
|---------|-----|
| `No active API key for user` | Sign in → Settings → save a provider key |
| `RateLimitError` from Anthropic | Wait — litellm fallback chain should catch this. If it's a daily cap, try a different provider. |
| browser-use times out on a job URL | LinkedIn/Indeed are anti-bot heavy — try a Greenhouse/Lever URL first. The fast-path crawl4ai is used for non-bot-walled sites. |
| open-design CV generation produces blank PDFs | Confirm the daemon is up (`curl http://localhost:4477/api/design-systems`). If down, the fallback HTML template is used (still ATS-safe). |

### "Just give me a clean reset"

```bash
./run.sh --stop                              # stop containers
docker volume rm $(docker volume ls -q | grep cvyne)  # delete data
rm -rf apps/web/node_modules apps/api/.venv  # delete deps
rm -rf .turbo .next                          # delete caches
./run.sh --setup                             # rebuild
./run.sh                                     # start
```

---

## 9. Where to learn more

- **Architecture:** [`CLAUDE.md`](CLAUDE.md), [`docs/architecture/`](docs/architecture/)
- **Per-agent work directions:** [`docs/agents/`](docs/agents/) — Codex (AI), Kiro (infra), Antigravity (frontend)
- **Open-source lib docs:**
  - browser-use → https://github.com/browser-use/browser-use
  - open-design → https://github.com/nexu-io/open-design
  - litellm → https://docs.litellm.ai/
  - instructor → https://python.useinstructor.com/
  - FastAPI → https://fastapi.tiangolo.com/
  - Next.js 15 → https://nextjs.org/docs
- **Issues:** open one at the project repo URL.
