# ADR-005: LiteLLM + Instructor for Multi-Provider LLM Access

**Status:** Accepted
**Date:** 2026-05-02
**Supersedes:** part of ADR-003

## Context

ADR-003 prescribed a custom `LLMClient` with provider switch statements. On review, this reinvents what `litellm` already does — better, with more providers, and battle-tested at scale.

## Decision

Use **`litellm`** as the provider router and **`instructor`** for structured Pydantic outputs. Our `LLMClient` is now a thin (~150 line) wrapper that adds:
- Anthropic prompt-cache injection policy
- Convenience constructors (`from_user_config`, `from_env`)
- Default fallback chain

Providers are addressed by litellm model strings: `anthropic/claude-sonnet-4-6`, `openai/gpt-4o`, `gemini/gemini-2.0-flash`, `ollama/llama3.2`.

## What We Get For Free (no code to write)

- 100+ providers (we listed 4 explicitly; users can BYOK any litellm-supported model string)
- Per-call cost tracking via `response._hidden_params["response_cost"]`
- Automatic retry with exponential backoff
- Fallback chains: if Anthropic rate-limits, try OpenAI, then Haiku
- Langfuse observability wired as a callback — every call traced
- In-memory + semantic response caching
- Streaming, async, batch — all unified
- Token counting, context window management

## Rationale

- **Less code** — deleted ~200 lines of switch statements
- **More providers** — every litellm-supported model is now usable
- **Better reliability** — fallback chains turn provider outages into invisible degradations
- **Better economics** — semantic cache + cost tracking surface waste
- **Vendor agnosticism** — when GPT-5 / Claude 5 / new models ship, no code change

## Consequences

- One more dependency (`litellm` is heavy, ~50MB)
- We're locked into litellm's API stability — historically very good, but a risk
- Some advanced provider features (e.g., Anthropic computer-use) require the bundled `chat_template` they expose; verify per-feature
