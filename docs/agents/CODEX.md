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

**`apps/api/core/llm.py` — `from_user_config`**

```python
@classmethod
def from_user_config(cls, user_id: str, provider: LLMProvider | None = None) -> "LLMClient":
    # 1. Import DB session (from core.db import async_session)
    # 2. Query: SELECT * FROM api_keys WHERE user_id=? AND is_active=TRUE
    # 3. If provider specified, filter by provider
    # 4. Decrypt key using AES-256-GCM with settings.encryption_key
    # 5. Return LLMClient(provider=row.provider, api_key=decrypted_key)
```

## Key Design Invariants You Must Preserve

1. **No prompt strings outside `prompts/`** — if you need a new prompt, register it
2. **`LLMClient` is the only SDK importer** — no `import anthropic` in service files
3. **Agents are stateless** — no `__init__` side effects, no class-level state
4. **Structured output everywhere** — return Pydantic models, not dicts or raw strings

## browser-use Integration Notes

browser-use expects a LangChain-compatible LLM. Bridge pattern:

```python
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

def _to_langchain_llm(self) -> BaseChatModel:
    match self.provider:
        case LLMProvider.ANTHROPIC:
            return ChatAnthropic(model=self.default_model, api_key=self.api_key)
        case LLMProvider.OPENAI:
            return ChatOpenAI(model=self.default_model, api_key=self.api_key)
```

Add `langchain-anthropic` and `langchain-openai` to pyproject.toml when you implement this.

## open-design Integration Notes

Install from source until PyPI release:
```
pip install git+https://github.com/nicktacular/open-design
```

Map `CVTheme` → design system name → open-design call. Verify the API shape from the repo before implementing. The interface in `design_agent.py` shows the expected behavior — adapt to actual library API.

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
