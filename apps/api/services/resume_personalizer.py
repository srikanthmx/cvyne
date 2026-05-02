"""Resume personalization service — uses prompt registry + LLM to tailor resumes."""

from __future__ import annotations

from core.llm import LLMClient, LLMProvider
from models.job import JDSchema
from models.resume import ResumeSchema, TailoredResumeSchema
from prompts.registry import PromptRegistry


class ResumePersonalizer:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm = llm_client or LLMClient.from_env(LLMProvider.ANTHROPIC)
        self._prompt = PromptRegistry.get("resume_personalize")

    async def personalize(self, resume: ResumeSchema, jd: JDSchema) -> TailoredResumeSchema:
        rendered = self._prompt.render(
            resume_json=resume.model_dump_json(indent=2),
            job_title=jd.title,
            company=jd.company,
            required_skills=jd.skills_required,
            job_description=jd.description,
        )
        result: TailoredResumeSchema = await self._llm.complete(
            rendered, structured_output=TailoredResumeSchema
        )
        return result
