"""
Resume PDF/DOCX parser — convert uploaded files into ResumeSchema.

Uses pymupdf4llm for PDF (LLM-friendly markdown extraction)
+ LLM call to map markdown → structured ResumeSchema.

This unblocks the user upload flow ("upload your existing resume").
"""

from __future__ import annotations

from pathlib import Path

from core.llm import LLMClient
from models.resume import ResumeSchema
from prompts.registry import PromptRegistry, PromptTemplate

PromptRegistry.register(
    PromptTemplate(
        name="resume_parse",
        version="v1.0.0",
        temperature=0.0,
        system_template="""You are a precise resume parser. Convert the provided resume text into structured JSON.

Rules:
- Extract ONLY information explicitly in the text
- Do not infer or fabricate any field
- For dates, use ISO format YYYY-MM-DD; if only year/month known, use YYYY-01-01 or YYYY-MM-01
- If end date is "Present" or missing, set to null
- Skills should be atomic (split "Python/Django" into ["Python", "Django"])
- Preserve original phrasing of bullet points""",
        user_template="""Resume content:
<resume>
{{ content }}
</resume>

Return the structured ResumeSchema JSON.""",
    )
)


class ResumeParserService:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm = llm_client or LLMClient.from_env()
        self._prompt = PromptRegistry.get("resume_parse")

    async def parse_file(self, file_path: Path) -> ResumeSchema:
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            content = self._extract_pdf(file_path)
        elif suffix in {".docx", ".doc"}:
            content = self._extract_docx(file_path)
        elif suffix in {".txt", ".md"}:
            content = file_path.read_text(encoding="utf-8")
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

        return await self._parse_content(content)

    async def parse_content(self, content: str) -> ResumeSchema:
        return await self._parse_content(content)

    def _extract_pdf(self, path: Path) -> str:
        """LLM-friendly markdown extraction via pymupdf4llm."""
        try:
            import pymupdf4llm
            return pymupdf4llm.to_markdown(str(path))
        except ImportError:
            import fitz  # PyMuPDF
            doc = fitz.open(str(path))
            return "\n\n".join(page.get_text() for page in doc)

    def _extract_docx(self, path: Path) -> str:
        try:
            from docx import Document
            doc = Document(str(path))
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except ImportError:
            raise RuntimeError("python-docx not installed — cannot parse .docx files")

    async def _parse_content(self, content: str) -> ResumeSchema:
        rendered = self._prompt.render(content=content[:12000])
        return await self._llm.complete(rendered, structured_output=ResumeSchema)
