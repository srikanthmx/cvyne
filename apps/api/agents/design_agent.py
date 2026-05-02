"""
Design Agent — wraps open-design for CV generation and PDF export.

Codex owns this file.
open-design: https://github.com/nicktacular/open-design (19 design skills, 71 design systems)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from models.job import CVTheme
from models.resume import TailoredResumeSchema


@dataclass
class FileRef:
    """Reference to a generated file in object storage."""

    s3_key: str
    filename: str
    mime_type: str
    size_bytes: int | None = None
    presigned_url: str | None = None


THEME_TO_DESIGN_SYSTEM: dict[CVTheme, str] = {
    CVTheme.ATS: "professional-ats",
    CVTheme.MODERN: "modern-minimal",
    CVTheme.CREATIVE: "creative-bold",
    CVTheme.PORTFOLIO: "portfolio-showcase",
}


class DesignAgent:
    """
    Stateless CV generation agent using open-design.

    Generates PDFs from structured resume data using design system templates.
    Each call is independent — no state between invocations.
    """

    def __init__(self, s3_client: object | None = None, output_dir: Path | None = None) -> None:
        self._s3_client = s3_client
        self._output_dir = output_dir or Path("/tmp/cvyne-cv")
        self._output_dir.mkdir(parents=True, exist_ok=True)

    async def generate_cv(
        self,
        resume: TailoredResumeSchema,
        theme: CVTheme,
        application_id: str,
        user_id: str,
    ) -> FileRef:
        """
        Generate a CV PDF from resume data using the specified theme.

        Returns a FileRef pointing to the uploaded S3 object.
        Raises RuntimeError if open-design generation fails.
        """
        design_system = THEME_TO_DESIGN_SYSTEM[theme]
        output_path = self._output_dir / f"{application_id}_{theme.value}.pdf"

        try:
            await self._generate_with_open_design(resume, design_system, output_path)
        except ImportError:
            # Fallback: generate plain HTML/PDF without open-design (dev mode)
            await self._generate_fallback_pdf(resume, output_path)

        s3_key = f"{user_id}/cvs/{application_id}/{theme.value}.pdf"
        file_size = output_path.stat().st_size

        if self._s3_client:
            await self._upload_to_s3(output_path, s3_key)

        return FileRef(
            s3_key=s3_key,
            filename=f"cv_{theme.value}.pdf",
            mime_type="application/pdf",
            size_bytes=file_size,
        )

    async def _generate_with_open_design(
        self, resume: TailoredResumeSchema, design_system: str, output_path: Path
    ) -> None:
        """
        TODO (Codex): implement open-design integration.

        open-design API surface (verify against actual library docs):
        - Load design system by name
        - Map ResumeSchema fields to design components
        - Export to PDF

        Reference: https://github.com/nicktacular/open-design
        """
        raise ImportError("open-design not yet integrated — using fallback")

    async def _generate_fallback_pdf(
        self, resume: TailoredResumeSchema, output_path: Path
    ) -> None:
        """Plain HTML → PDF fallback using weasyprint (for dev/testing)."""
        try:
            import weasyprint

            html = self._resume_to_html(resume)
            weasyprint.HTML(string=html).write_pdf(str(output_path))
        except ImportError:
            # Absolute fallback: write a placeholder file
            output_path.write_bytes(b"%PDF-1.4 placeholder")

    def _resume_to_html(self, resume: TailoredResumeSchema) -> str:
        """Minimal ATS-safe HTML template for fallback PDF generation."""
        exp_html = "\n".join(
            f"<div class='role'><b>{e.role}</b> — {e.company} ({e.start} – {e.end or 'Present'})"
            f"<ul>{''.join(f'<li>{b}</li>' for b in e.bullets)}</ul></div>"
            for e in resume.experience
        )
        return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>body{{font-family:Arial,sans-serif;font-size:11pt;margin:40px}}
h1{{font-size:20pt;margin-bottom:4px}}h2{{font-size:13pt;border-bottom:1px solid #333}}
.role{{margin-bottom:12px}}</style></head><body>
<h1>{resume.name}</h1>
<p>{resume.email}{' | ' + resume.phone if resume.phone else ''}</p>
{'<p>' + resume.summary + '</p>' if resume.summary else ''}
<h2>Skills</h2><p>{', '.join(resume.skills)}</p>
<h2>Experience</h2>{exp_html}
</body></html>"""

    async def _upload_to_s3(self, file_path: Path, s3_key: str) -> None:
        """TODO (Kiro): implement S3 upload via aioboto3."""
        pass
