# ADR-003: Single LLMClient Abstraction for All Providers

**Status:** Accepted
**Date:** 2026-05-02

## Context

The product supports BYOK (Bring Your Own Key) for multiple LLM providers. Services should not know or care which provider is active.

## Decision

`apps/api/core/llm.py` is the **only** file that imports provider SDKs. All services receive an `LLMClient` instance (injected or default-constructed). Provider-specific behavior is isolated to private methods.

`LLMClient.from_user_config(user_id)` loads the user's stored encrypted API key and returns the correct provider client.

Structured output is handled uniformly: Anthropic uses tool_use + input extraction; OpenAI uses beta.chat.completions.parse; others TBD.

## Rationale

- Zero-change provider swap at service layer
- Easier to add new providers (Gemini, Mistral, etc.)
- Single place for rate limiting, retry logic, and telemetry
- Prompt caching policy centralized

## Consequences

- `core/llm.py` is high-complexity and high-impact — requires ADR to change
- Structured output parity must be maintained across providers
- Streaming interface may need provider-specific workarounds
