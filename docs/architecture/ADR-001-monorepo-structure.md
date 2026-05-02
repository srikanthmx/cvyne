# ADR-001: Turborepo Monorepo with Next.js + FastAPI

**Status:** Accepted
**Date:** 2026-05-02
**Deciders:** Architect

## Context

AutoApply AI has three distinct workloads:
1. Browser-facing UI (React/Next.js)
2. AI orchestration, browser automation, CV generation (Python)
3. Shared type contracts between frontend and backend

## Decision

Use a **Turborepo monorepo** with:
- `apps/web` — Next.js 15 (TypeScript)
- `apps/api` — FastAPI (Python, managed separately by uv)
- `packages/shared-types` — TypeScript interfaces that mirror Python Pydantic models

Python and Node.js coexist in the same repo but use separate package managers (pnpm for Node, uv for Python). Turbo orchestrates Node.js tasks only; Python tasks use a Makefile in `apps/api/`.

## Rationale

- Single repo = single source of truth for types, easier cross-cutting changes
- Turborepo handles caching and parallel execution for Node workspaces
- FastAPI chosen over Node.js backend for Python AI ecosystem compatibility (browser-use, LangChain, etc.)
- Shared types as a package prevents frontend/backend drift

## Consequences

- Developers need both Node.js 20+ and Python 3.12+ installed
- Type drift still possible if `shared-types` and Pydantic models diverge — enforced by CI type-check step
- Python API not orchestrated by Turbo — started separately or via Docker Compose
