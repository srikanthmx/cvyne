# Kiro Work Instructions — Infrastructure & Data Layer

> Read CLAUDE.md and AGENTS.md first. This file is Kiro-specific detail.

## Your Domain

You are the foundation. Without your work, Codex and Antigravity can't run. Build solid ground.

## Starting Point (what exists)

- `infrastructure/docker/docker-compose.yml` — complete, ready to run
- `apps/api/core/config.py` — Pydantic Settings, complete
- `apps/api/workers/celery_app.py` — Celery config, complete
- `apps/api/workers/tasks.py` — task skeletons with `NotImplementedError`
- DB schema defined in AGENTS.md — needs SQLAlchemy models + Alembic migration

## First Thing to Build

**Start the infra:**
```bash
docker compose -f infrastructure/docker/docker-compose.yml up -d
```

Then implement `apps/api/core/db.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import settings

engine = create_async_engine(settings.database_url, echo=not settings.is_production)
async_session = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
```

## Database Models (implement in `apps/api/db/models.py`)

Match exactly the schema in AGENTS.md. Key notes:
- `api_keys.encrypted_key` — store AES-256-GCM ciphertext (base64 encoded)
- `applications.status` — use SQLAlchemy `Enum` type
- `resumes.data` — `JSONB` column via `sqlalchemy.dialects.postgresql.JSONB`
- All tables have `created_at TIMESTAMPTZ DEFAULT NOW()`

## Alembic Setup

```bash
cd apps/api
alembic init alembic
# Edit alembic/env.py to use async engine and import db.models.Base
alembic revision --autogenerate -m "initial_schema"
alembic upgrade head
```

## Encryption Implementation

```python
# core/security.py
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

def encrypt_api_key(plaintext: str, key_hex: str) -> str:
    key = bytes.fromhex(key_hex)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ct).decode()

def decrypt_api_key(ciphertext_b64: str, key_hex: str) -> str:
    key = bytes.fromhex(key_hex)
    aesgcm = AESGCM(key)
    data = base64.b64decode(ciphertext_b64)
    nonce, ct = data[:12], data[12:]
    return aesgcm.decrypt(nonce, ct, None).decode()
```

## Celery Task Implementation (`workers/tasks.py`)

For `process_application_task`:

```python
async def _run():
    async with async_session() as db:
        # 1. Load application from DB
        app = await db.get(Application, uuid.UUID(application_id))
        
        # 2. Load job + resume
        job = await db.get(Job, app.job_id)
        resume_row = await db.get(Resume, app.resume_id)
        
        # 3. Update status → processing
        app.status = "processing"
        await db.commit()
        
        # 4. Publish to Redis pub/sub
        r = redis.from_url(settings.redis_url)
        
        # 5. Run orchestrator, publish each event
        from services.orchestrator import OrchestratorService
        orch = OrchestratorService()
        resume = ResumeSchema.model_validate(resume_row.data)
        
        async for event in orch.run_application(...):
            r.publish(f"app:{application_id}", event.model_dump_json())
            app.status = event.status
            app.attempts = (app.attempts or 0) + 1
            await db.commit()
```

## Redis Pub/Sub for SSE

The SSE endpoint in `routers/applications.py` needs to subscribe:

```python
async def event_generator():
    r = redis.asyncio.from_url(settings.redis_url)
    pubsub = r.pubsub()
    await pubsub.subscribe(f"app:{application_id}")
    
    async for message in pubsub.listen():
        if message["type"] == "message":
            yield {"event": "status_update", "data": message["data"]}
            data = json.loads(message["data"])
            if data["status"] in {"submitted", "failed", "requires_human"}:
                break
```

## MinIO Bucket Setup

```bash
# In infrastructure/scripts/setup_minio.sh
mc alias set local http://localhost:9000 minioadmin minioadmin
mc mb local/cvyne
mc policy set public local/cvyne/public  # only for dev
```

## Health Check Implementation

```python
@app.get("/health/deep")
async def health_deep():
    checks = {}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as e:
        checks["db"] = f"error: {e}"
    
    try:
        r = redis.from_url(settings.redis_url)
        r.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"
    
    status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, **checks}
```

## Makefile for Python Tasks

```makefile
# apps/api/Makefile
dev:
	uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

worker:
	uv run celery -A workers.celery_app worker --loglevel=info

beat:
	uv run celery -A workers.celery_app beat --loglevel=info

migrate:
	uv run alembic upgrade head

test:
	uv run pytest

lint:
	uv run ruff check . && uv run ruff format --check .
```
