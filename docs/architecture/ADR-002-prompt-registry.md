# ADR-002: Prompt-as-Code with Versioned Registry

**Status:** Accepted
**Date:** 2026-05-02

## Context

AI-powered systems suffer from "prompt sprawl" — strings scattered across services, untested, unversioned, inconsistently cached.

## Decision

All prompts live in `apps/api/prompts/` as structured `PromptTemplate` objects registered in `PromptRegistry`. No inline prompt strings anywhere else.

Each template has:
- `name` — unique key
- `version` — semver string
- `system_template` / `user_template` — Jinja2 templates
- `metadata` — owner, eval_metrics

Prompts are automatically cache-eligible: system prompts >1024 tokens get `cache_control: ephemeral` injected by `LLMClient` when using Anthropic.

## Rationale

- **Testability**: prompts are units that can be evaluated independently
- **Auditability**: version history of what prompt was used per application
- **Cost control**: automatic caching reduces Anthropic API costs by 60-90% for repeated system prompts
- **Multi-model**: same template renders for any provider

## Consequences

- All service devs (Codex) must register prompts — no bypassing registry
- Prompt changes require version bumps — backward-compatible by default
- Adds Jinja2 as a dependency and requires care with template injection (use `StrictUndefined`)
