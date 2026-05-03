# Codex Work Instructions — AI Backend

> Read CLAUDE.md and AGENTS.md first. This file is Codex-specific detail.

## Your Domain

You own the AI brain of this system. Everything that makes AutoApply AI intelligent is your responsibility.

## Starting Point (what exists)

The scaffold is built. These files have correct interfaces but incomplete implementations:
- `apps/api/core/llm.py` — `from_user_config`, `_gemini_complete`, `_ollama_complete` are `NotImplementedError`
- `apps/api/agents/browser_agent.py` — real browser-use integration needs wiring
- `apps/api/agents/design_agent.py` — `_generate_with_open_design` needs implementation
- `apps/api/services/orchestrator.py` — complete
- `apps/api/prompts/` — all 4 templates registered, tune them

## First Thing to Build

**`apps/api/core/llm.py` — `from_user_config`** (the only stub left after litellm migration)

```python
@classmethod
async def from_user_config(cls, user_id: str, provider: LLMProvider | None = None) -> "LLMClient":
    from sqlalchemy import select
    from core.db import async_session_factory
    from core.security import decrypt_api_key
    from db.models import ApiKey

    async with async_session_factory() as db:
        stmt = select(ApiKey).where(ApiKey.user_id == user_id, ApiKey.is_active == True)
        if provider:
            stmt = stmt.where(ApiKey.provider == provider.value)
        row = (await db.execute(stmt)).scalars().first()
        if not row:
            raise ValueError(f"No active API key for user {user_id}")

    plaintext = decrypt_api_key(row.encrypted_key, settings.encryption_key)
    return cls(provider=LLMProvider(row.provider), api_key=plaintext)
```

Everything else (provider switching, retries, cost tracking, prompt caching, Langfuse tracing) is handled by `litellm` — already wired in `core/llm.py`.

## Key Design Invariants You Must Preserve

1. **No prompt strings outside `prompts/`** — if you need a new prompt, register it
2. **`LLMClient` is the only SDK importer** — no `import anthropic` in service files
3. **Agents are stateless** — no `__init__` side effects, no class-level state
4. **Structured output everywhere** — return Pydantic models, not dicts or raw strings

## browser-use Integration Notes

**Repo:** https://github.com/browser-use/browser-use
**DO NOT** wrap in LangChain. browser-use ships its own LLM clients:

```python
from browser_use import Agent, Browser, ChatBrowserUse
from browser_use.llm import ChatAnthropic, ChatOpenAI, ChatGoogle

# Pass directly to Agent — already implemented in agents/browser_agent.py
agent = Agent(task="...", llm=ChatAnthropic(model="claude-sonnet-4-6", api_key=key), browser=Browser())
```

After install, run `uv run playwright install chromium` once.
Python >= 3.11 required (we're on 3.12).

When wiring user BYOK keys: `BrowserAgent(provider=LLMProvider.X, api_key=user_key)` — `_build_llm()` already routes correctly.

## open-design Integration Notes

**Repo:** https://github.com/nexu-io/open-design
**It is NOT a Python library.** It is a TypeScript Express + SQLite daemon that orchestrates local agent CLIs (claude, codex, cursor-agent, gemini, etc.) and produces HTML artifacts.

We treat it as a **sidecar service** and talk to it over HTTP. The client lives in `apps/api/agents/design_agent.py` (`OpenDesignClient`). Already implemented:
- `POST /api/chat` (SSE) → returns concatenated artifact text
- `POST /api/artifacts/save`
- `GET /api/design-systems` — call on startup to confirm theme slugs
- `GET /api/skills`

To run open-design locally: `docker compose --profile full up -d` (builds from GitHub).

**On first integration run**, call `GET /api/design-systems` and verify our `THEME_TO_DESIGN_SYSTEM` map matches actual slugs. Update if needed.

**BYOK passthrough:** open-design's `POST /api/proxy/stream` accepts `{baseUrl, apiKey, model}` for any OpenAI-compatible endpoint. If we want the user's BYOK key to drive open-design's design generation (rather than the daemon's local CLI), use this proxy. For MVP, use the local agent CLI — simpler and free.

**Artifact extraction:** open-design returns `<artifact type="text/html">...</artifact>` blocks in the chat stream. `_extract_artifact()` already handles this regex parse.

**PDF rendering:** open-design itself uses browser print → PDF. We use `weasyprint` locally because it's a single Python dep and works headless. Production can swap to Playwright print for fidelity.

## Prompt Tuning Guidelines

When iterating prompts:
- Always bump `version` (e.g., `v1.0.0` → `v1.1.0`)
- Add eval tests in `apps/api/tests/` to measure improvement
- No-fabrication constraint in `resume_personalize` is absolute — test for it

## Testing Your Work

```bash
cd apps/api
pytest tests/unit/test_llm.py -v
pytest tests/unit/test_prompts.py -v
pytest tests/integration/test_orchestrator.py -v
```

Write tests before implementing if possible. Integration tests need Docker services running.
