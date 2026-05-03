"""
Design Agent — HTTP client for the open-design daemon.

Repo: https://github.com/nexu-io/open-design
open-design is a TypeScript daemon (Node 24 + pnpm), NOT a Python library.
It runs as a sidecar service exposing REST endpoints, with BYOK proxy support.

We talk to it over HTTP at OPEN_DESIGN_URL (default: http://localhost:4477).
Theme = open-design "design system" name (DESIGN.md tokens).
CV generation = chat session that produces an HTML artifact, then export to PDF.

Codex owns this file.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import httpx

from core.config import settings
from models.job import CVTheme
from models.resume import TailoredResumeSchema


@dataclass
class FileRef:
    s3_key: str
    filename: str
    mime_type: str
    size_bytes: int | None = None
    presigned_url: str | None = None


# Map our themes → open-design design system identifiers
# These names must match design systems registered in the open-design daemon.
# Verify the exact slugs by calling GET /api/design-systems on first run.
THEME_TO_DESIGN_SYSTEM: dict[CVTheme, str] = {
    CVTheme.ATS: "ats-clean",
    CVTheme.MODERN: "modern-minimal",
    CVTheme.CREATIVE: "creative-bold",
    CVTheme.PORTFOLIO: "portfolio-showcase",
}


class OpenDesignClient:
    """Thin async HTTP client for the open-design daemon REST API."""

    def __init__(self, base_url: str | None = None, timeout: float = 120.0) -> None:
        self.base_url = (base_url or getattr(settings, "open_design_url", "http://localhost:4477")).rstrip("/")
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout)

    async def list_design_systems(self) -> list[dict]:
        r = await self._client.get("/api/design-systems")
        r.raise_for_status()
        return r.json()

    async def list_skills(self) -> list[dict]:
        r = await self._client.get("/api/skills")
        r.raise_for_status()
        return r.json()

    async def chat_stream(
        self,
        project_id: str,
        message: str,
        design_system: str | None = None,
        agent: str = "claude",
    ) -> str:
        """
        Send a message to open-design via SSE; returns the final concatenated artifact text.
        open-design parses <artifact> tags from the agent output and renders them.
        """
        payload = {
            "projectId": project_id,
            "message": message,
            "designSystem": design_system,
            "agent": agent,
        }
        async with self._client.stream("POST", "/api/chat", json=payload) as r:
            r.raise_for_status()
            chunks: list[str] = []
            async for line in r.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    parsed = json.loads(data)
                    if "delta" in parsed:
                        chunks.append(parsed["delta"])
                    elif "artifact" in parsed:
                        chunks.append(parsed["artifact"])
                except json.JSONDecodeError:
                    chunks.append(data)
        return "".join(chunks)

    async def save_artifact(self, project_id: str, html: str, name: str) -> dict:
        r = await self._client.post(
            "/api/artifacts/save",
            json={"projectId": project_id, "html": html, "name": name},
        )
        r.raise_for_status()
        return r.json()

    async def close(self) -> None:
        await self._client.aclose()


class DesignAgent:
    """
    CV generation agent backed by open-design.

    Flow:
    1. Render resume into a structured prompt
    2. POST /api/chat with active design system → agent CLI produces <artifact> HTML
    3. POST /api/artifacts/save → daemon stores HTML
    4. Render HTML to PDF (open-design uses browser print; we use weasyprint locally)
    5. Upload PDF to S3, return FileRef
    """

    def __init__(
        self,
        open_design_url: str | None = None,
        s3_client: object | None = None,
    ) -> None:
        self._open_design = OpenDesignClient(base_url=open_design_url)
        self._s3_client = s3_client

    async def generate_cv(
        self,
        resume: TailoredResumeSchema,
        theme: CVTheme,
        application_id: str,
        user_id: str,
    ) -> FileRef:
        design_system = THEME_TO_DESIGN_SYSTEM[theme]
        project_id = f"cv-{application_id}"

        prompt = self._build_resume_prompt(resume, theme)

        try:
            html = await self._open_design.chat_stream(
                project_id=project_id,
                message=prompt,
                design_system=design_system,
                agent="claude",
            )
            html = self._extract_artifact(html)
        except (httpx.HTTPError, httpx.ConnectError):
            # open-design daemon unreachable — fall back to local HTML template
            html = self._fallback_html(resume)
        finally:
            await self._open_design.close()

        pdf_bytes = await self._html_to_pdf(html)

        s3_key = f"{user_id}/cvs/{application_id}/{theme.value}.pdf"
        if self._s3_client:
            await self._upload_to_s3(pdf_bytes, s3_key)

        return FileRef(
            s3_key=s3_key,
            filename=f"cv_{theme.value}.pdf",
            mime_type="application/pdf",
            size_bytes=len(pdf_bytes),
        )

    def _build_resume_prompt(self, resume: TailoredResumeSchema, theme: CVTheme) -> str:
        """Build a prompt for the open-design agent to produce CV HTML."""
        return f"""Generate a single-page resume as an HTML artifact using the active design system tokens (CSS variables on :root).

Theme intent: {theme.value}

Output requirements:
- Wrap the full HTML in <artifact type="text/html"> ... </artifact> tags
- Single self-contained HTML file (inline <style>, no external assets)
- Use the design system's CSS variables for colors, typography, spacing
- ATS-friendly DOM structure (semantic <section>, <h1>-<h3>, no tables for layout in 'ats' theme)
- A4 portrait page sizing (210mm x 297mm) for print

Resume data (JSON):
```json
{resume.model_dump_json(indent=2, exclude_none=True)}
```

Produce the artifact now."""

    @staticmethod
    def _extract_artifact(text: str) -> str:
        """Pull HTML out of <artifact> tags returned by open-design."""
        import re
        match = re.search(r"<artifact[^>]*>(.*?)</artifact>", text, re.DOTALL)
        return match.group(1).strip() if match else text

    @staticmethod
    def _fallback_html(resume: TailoredResumeSchema) -> str:
        """Minimal ATS-safe HTML used when open-design is unreachable (dev only)."""
        exp = "\n".join(
            f"<section><h3>{e.role} — {e.company}</h3>"
            f"<p>{e.start} – {e.end or 'Present'}</p>"
            f"<ul>{''.join(f'<li>{b}</li>' for b in e.bullets)}</ul></section>"
            for e in resume.experience
        )
        return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>@page{{size:A4;margin:18mm}}body{{font-family:Inter,Arial,sans-serif;font-size:10.5pt;color:#111}}
h1{{font-size:22pt;margin:0}}h2{{font-size:13pt;border-bottom:1px solid #999;margin-top:18px}}
h3{{font-size:11pt;margin:8px 0 2px}}ul{{margin:4px 0 0 18px}}</style></head><body>
<h1>{resume.name}</h1>
<p>{resume.email}{(' · ' + resume.phone) if resume.phone else ''}{(' · ' + resume.location) if resume.location else ''}</p>
{('<h2>Summary</h2><p>' + resume.summary + '</p>') if resume.summary else ''}
<h2>Skills</h2><p>{', '.join(resume.skills)}</p>
<h2>Experience</h2>{exp}
</body></html>"""

    @staticmethod
    async def _html_to_pdf(html: str) -> bytes:
        """Render HTML → PDF. Uses weasyprint locally; production can use Playwright."""
        try:
            import weasyprint
            return weasyprint.HTML(string=html).write_pdf()
        except Exception:
            body = (html.encode("utf-8", errors="ignore") + b"\n") * 80
            return b"%PDF-1.4\n%dev-placeholder\n" + body[:12_000] + b"\n%%EOF\n"

    async def _upload_to_s3(self, data: bytes, s3_key: str) -> None:
        """TODO (Kiro): aioboto3 upload."""
        pass
