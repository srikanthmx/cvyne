"""ATS optimization service."""

from __future__ import annotations

from core.llm import LLMClient, LLMProvider
from models.job import JDSchema
from models.resume import TailoredResumeSchema
from prompts.registry import PromptRegistry


class ATSOptimizer:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm = llm_client or LLMClient.from_env(LLMProvider.ANTHROPIC)
        self._prompt = PromptRegistry.get("ats_optimize")

    async def optimize(self, resume: TailoredResumeSchema, jd: JDSchema) -> TailoredResumeSchema:
        keywords = list(set(jd.skills_required + jd.skills_preferred))
        rendered = self._prompt.render(
            resume_json=resume.model_dump_json(indent=2),
            keywords=keywords,
        )
        return await self._llm.complete(rendered, structured_output=TailoredResumeSchema)
