# ADR-004: Open-Source Integrations — browser-use (lib) and open-design (sidecar)

**Status:** Accepted
**Date:** 2026-05-02

## Context

Two foundational open-source projects power our differentiation:
- **browser-use** (https://github.com/browser-use/browser-use) — agentic browser control
- **open-design** (https://github.com/nexu-io/open-design) — AI-driven design generation

These have different distribution models and require different integration strategies.

## Decision

### browser-use → in-process Python library
- Add as direct dependency in `apps/api/pyproject.toml`
- Use bundled LLM clients (`ChatBrowserUse`, `ChatAnthropic`, `ChatOpenAI`, `ChatGoogle`) — **no LangChain wrappers**
- All access goes through `apps/api/agents/browser_agent.py`
- `BrowserAgent` accepts `provider`, `api_key`, `model` so user BYOK keys flow through

### open-design → sidecar HTTP daemon
- open-design is a TypeScript Express + SQLite service, not a Python library
- Run as a separate container in docker-compose under the `full` profile
- Communicate via REST + SSE at `OPEN_DESIGN_URL` (default `http://localhost:4477`)
- All access goes through `apps/api/agents/design_agent.py` → `OpenDesignClient`
- Theme map (`THEME_TO_DESIGN_SYSTEM`) verified at startup against `GET /api/design-systems`
- HTML artifact extracted from `<artifact>` tags, rendered to PDF locally via `weasyprint`

## Rationale

**Why no LangChain for browser-use?**
- browser-use's bundled clients are tuned for the agent loop (prompt format, tool schema)
- Adds zero dependency surface
- Provider parity is maintained by browser-use upstream — we stay current automatically

**Why sidecar (not library) for open-design?**
- It is fundamentally a Node.js orchestration daemon — not portable into Python
- Sidecar pattern keeps language boundaries clean
- BYOK proxy and skill registry are server features, not embeddable
- Clear scaling story — can move daemon to dedicated host or k8s later
- Failure isolation — daemon crash doesn't take down the FastAPI process

## Consequences

- **Operational complexity:** dev needs Docker (already true) + understanding the `full` profile
- **Network hop:** every CV generation is an HTTP roundtrip — acceptable given 2-10s LLM latency dominates
- **Fallback path:** `_fallback_html()` in `DesignAgent` handles daemon unreachable scenarios for dev
- **Theme drift risk:** if open-design updates design-system slugs, our map breaks — startup health check should validate

## Open Questions for Codex

1. Should we use open-design's `/api/proxy/stream` (BYOK passthrough) so user keys drive design generation? Or is the local CLI mode sufficient? (MVP: local CLI; revisit when users complain about cost.)
2. Do we host our own design system (DESIGN.md tokens) tuned for ATS resumes, or rely on open-design defaults? (Recommend: contribute an `ats-clean` design system upstream.)
