"""Cover letter generation service."""

from __future__ import annotations

from core.llm import LLMClient, LLMProvider
from models.job import JDSchema
from models.resume import TailoredResumeSchema
from prompts.registry import PromptRegistry


class CoverLetterService:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm = llm_client or LLMClient.from_env(LLMProvider.ANTHROPIC)
        self._prompt = PromptRegistry.get("cover_letter")

    async def generate(self, resume: TailoredResumeSchema, jd: JDSchema) -> str:
        top_bullets = [
            bullet
            for exp in resume.experience[:2]
            for bullet in exp.bullets[:3]
        ]
        current_role = (
            f"{resume.experience[0].role} at {resume.experience[0].company}"
            if resume.experience
            else "Professional"
        )
        rendered = self._prompt.render(
            name=resume.name,
            current_role=current_role,
            top_skills=resume.skills[:6],
            top_bullets=top_bullets,
            company=jd.company,
            job_title=jd.title,
            key_requirements=jd.skills_required[:5],
        )
        return await self._llm.complete(rendered)  # type: ignore[return-value]
