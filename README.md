# AutoApply AI

> Automate job applications end-to-end: extract JD → personalize resume → generate ATS PDF → autofill the form → submit.

Multi-LLM (BYOK), browser automation, and design generation all stitched together — the system applies to jobs while you sleep.

## Quick start

```bash
./run.sh --setup     # one time: install deps + run migrations
# fill in apps/api/.env and apps/web/.env.local (see GETTING_STARTED.md)
./run.sh             # starts everything
```

Open http://localhost:3000.

## Documentation

| Doc | What |
|-----|------|
| [`GETTING_STARTED.md`](GETTING_STARTED.md) | **Start here.** Full install + run guide with API key links and troubleshooting. |
| [`CLAUDE.md`](CLAUDE.md) | Architecture overview — read before making changes |
| [`AGENTS.md`](AGENTS.md) | Agent ownership, schema contracts, SSE event format |
| [`docs/architecture/`](docs/architecture/) | Architecture Decision Records |
| [`docs/agents/`](docs/agents/) | Per-agent work directions (Codex / Kiro / Antigravity) |

## Stack

Next.js 15 · FastAPI · litellm + instructor · browser-use · open-design (sidecar) · Celery + Redis · PostgreSQL · MinIO · Clerk · Langfuse

## Top-level commands

```bash
./run.sh              # start everything
./run.sh --stop       # tear down docker services
./run.sh --setup      # reinstall deps + migrations
make help             # see all targets
pnpm types:gen        # regenerate TS types from FastAPI OpenAPI
```
