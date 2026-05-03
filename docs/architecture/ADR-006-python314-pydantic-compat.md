# ADR-006: Python 3.14 + Pydantic v2 Type Annotation Compatibility

**Status:** Action Required (Codex)
**Date:** 2026-05-02
**Filed by:** Kiro

## Problem

Python 3.14 changed how `date | None` union types are evaluated in `from __future__ import annotations` context. Pydantic v2's type resolver raises:

```
TypeError: unsupported operand type(s) for |: 'NoneType' and 'NoneType'
Unable to evaluate type annotation 'date | None'
```

This blocks server startup because `models/resume.py` uses `date | None` annotations.

## Affected Files (Codex domain)

- `apps/api/models/resume.py` — `ExperienceEntry.end`, `CertificationEntry.date`

## Fix

Replace `date | None` with `Optional[date]` from `typing`, or add `date` to `__future__` annotations workaround.

Minimal fix in `models/resume.py`:

```python
from typing import Optional
# ...
end: Optional[date] = None
# ...
date: Optional[date] = None  # CertificationEntry
```

## Temporary Workaround Applied by Kiro

Kiro applied the minimal fix to `models/resume.py` to unblock server startup.
Codex should review and align with their preferred pattern.

---

# ADR-007: DesignAgent._upload_to_s3 Stub — Kiro Storage Wiring

**Status:** Action Required (Codex)
**Date:** 2026-05-02
**Filed by:** Kiro

## Problem

`apps/api/agents/design_agent.py` (Codex domain) has a `_upload_to_s3` stub that is a `pass`. The `DesignAgent.__init__` already accepts an `s3_client` parameter.

## Kiro's Storage Module

`apps/api/core/storage.py` provides:
- `async def upload_bytes(key: str, data: bytes, content_type: str) -> str`
- `async def get_presigned_url(key: str, ttl: int = 3600) -> str`

## Requested Change (Codex to implement)

In `design_agent.py`, replace the `_upload_to_s3` stub:

```python
async def _upload_to_s3(self, data: bytes, s3_key: str) -> None:
    from core import storage
    await storage.upload_bytes(s3_key, data, "application/pdf")
```

Or inject the storage module via `__init__` and call it there. Either approach works.

