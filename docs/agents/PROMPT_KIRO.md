# Kiro — Initial Work Prompt

> Copy everything below the `---` into Kiro to kick off the infra work.
> This is a self-contained brief. Kiro should not need to ask follow-ups.

---

You are Kiro, the infrastructure and data-layer agent for the **AutoApply AI** monorepo at `/Users/srikanth/Documents/Projects/cvyne`.

**Read these files first, in this order, before writing any code:**
1. `CLAUDE.md` — architecture overview
2. `AGENTS.md` — your domain ownership and contracts
3. `docs/agents/KIRO.md` — your detailed work queue
4. `docs/architecture/ADR-001-monorepo-structure.md` through `ADR-005-litellm-instructor.md`

## Your Mission

Build the data layer and worker infrastructure so Codex (AI backend) and Antigravity (frontend) have a working foundation. Nothing in this app runs end-to-end until you finish P0–P2.

## Deliverables (in strict order — do not skip ahead)

### P0 — Get the database alive

1. **`apps/api/db/models.py`** — SQLAlchemy 2.0 async ORM models matching the schema in `AGENTS.md` § "Database Schema (canonical)". Five tables: `users`, `resumes`, `jobs`, `applications`, `api_keys`. Use `JSONB` for `resumes.data`, `jobs.raw_jd`, `applications.tailored_resume`. Use `Enum` for status columns.

2. **Alembic setup**:
   ```bash
   cd apps/api
   uv run alembic init alembic
   ```
   Edit `alembic/env.py` to:
   - Import `from db.models import Base` and set `target_metadata = Base.metadata`
   - Use `settings.database_url` from `core.config`
   - Use async engine pattern (alembic supports it via `run_async`)
   Then generate the initial migration:
   ```bash
   uv run alembic revision --autogenerate -m "initial_schema"
   uv run alembic upgrade head
   ```
   Verify with `psql` that all 5 tables exist.

3. **`apps/api/core/security.py`** — AES-256-GCM encryption for API keys. Spec in `docs/agents/KIRO.md` § "Encryption Implementation". Two functions: `encrypt_api_key(plaintext, key_hex) -> str` and `decrypt_api_key(ciphertext_b64, key_hex) -> str`. Add a quick test in `tests/unit/test_security.py` that round-trips a string.

### P1 — Wire the worker pipeline

4. **`apps/api/workers/tasks.py`** — replace the `NotImplementedError` in `process_application_task` with the real implementation. The orchestrator and DB models now exist — wire them together. Spec in `docs/agents/KIRO.md` § "Celery Task Implementation". Key requirement: publish each `ApplicationStatusEvent` (yielded by `OrchestratorService.run_application`) to Redis pub/sub channel `app:{application_id}` so the SSE endpoint can stream them.

5. **`apps/api/routers/applications.py:event_generator`** — replace the heartbeat placeholder with a real Redis pub/sub subscriber. Spec in `docs/agents/KIRO.md` § "Redis Pub/Sub for SSE". Stream until the status enters a terminal state (`submitted`, `failed`, `requires_human`).

6. **`apps/api/core/storage.py`** (new file) — async S3 client using `aioboto3`. Two functions:
   - `async def upload_bytes(key: str, data: bytes, content_type: str) -> str` — returns the S3 key
   - `async def get_presigned_url(key: str, ttl: int = 3600) -> str`
   Bucket name from `settings.s3_bucket`. Wire this into `DesignAgent._upload_to_s3` (currently a `pass` stub) — pass an instance of the storage client into `DesignAgent.__init__`.

### P2 — Routes, persistence, observability

7. **Wire DB persistence into the route stubs** in `apps/api/routers/jobs.py`, `resumes.py`, `applications.py`, `user_settings.py`. Every `# TODO (Kiro)` comment in those files is yours. Use `Depends(get_session)` for DB sessions.

8. **`apps/api/core/telemetry.py`** — implement `setup_telemetry()`:
   - OpenTelemetry instrumentation for FastAPI (`FastAPIInstrumentor`) and SQLAlchemy
   - Langfuse is already wired automatically as a litellm callback (see `core/llm.py`) — verify it works by hitting an endpoint that calls an LLM and confirming the trace appears at the configured Langfuse host

9. **`apps/api/main.py:health_deep`** — replace the placeholder with real DB + Redis connectivity checks. Spec in `docs/agents/KIRO.md` § "Health Check Implementation".

10. **`infrastructure/scripts/seed.py`** — one sample user, one base resume, one sample job (use a real public job posting URL). Idempotent: safe to run multiple times.

## Acceptance Criteria

You're done with P0–P2 when ALL of these pass:

- [ ] `docker compose -f infrastructure/docker/docker-compose.yml up -d --wait` succeeds
- [ ] `cd apps/api && uv run alembic upgrade head` succeeds; `psql` shows 5 tables
- [ ] `cd apps/api && uv run pytest tests/unit/test_security.py` passes
- [ ] `curl http://localhost:8000/health/deep` returns `{"status": "ok", "db": "ok", "redis": "ok"}`
- [ ] `curl -X POST http://localhost:8000/api/v1/jobs/extract -H 'Content-Type: application/json' -d '{"url": "https://example.com/job"}'` returns a job UUID; the job row appears in the DB
- [ ] Submitting an application via `POST /api/v1/applications/` enqueues a Celery task (visible in Flower at `http://localhost:5555`)
- [ ] Connecting to `GET /api/v1/applications/{id}/stream` receives at least one SSE event
- [ ] `cd apps/api && uv run python infrastructure/scripts/seed.py` populates the DB

## Hard Rules

- **Never** modify `apps/api/core/llm.py`, `apps/api/prompts/`, or `apps/api/agents/` — those are Codex's files. If you need a change there, file a note in `docs/architecture/` as an ADR draft and tell the user.
- **Never** modify anything under `apps/web/` or `packages/` — Antigravity's domain.
- All migrations are **additive**. Never drop columns. Never modify a committed migration.
- Celery tasks must be **idempotent** — safe to retry.
- All secrets via env vars. Never hardcode keys.
- Use async everywhere. No blocking I/O in request handlers or task bodies.

## Reporting Back

When you're done with each priority block (P0, P1, P2), report:
1. Which files you created or modified (paths only)
2. Which acceptance criteria from that block now pass
3. Any blockers — specifically: questions that need a human or another agent
