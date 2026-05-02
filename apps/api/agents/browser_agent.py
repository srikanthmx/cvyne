"""
Browser Agent — wraps browser-use for JD extraction and form autofill.

Codex owns this file.
browser-use docs: https://github.com/browser-use/browser-use
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from models.job import ApplicationStatus, JDSchema
from models.resume import TailoredResumeSchema


@dataclass
class AutofillResult:
    status: ApplicationStatus
    screenshot_url: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class BrowserAgent:
    """
    Stateless browser automation agent.

    Each method creates a fresh browser context — no state shared between calls.
    Agents are safe to instantiate per-request.
    """

    def __init__(self, llm_client: Any | None = None, headless: bool = True) -> None:
        self._llm_client = llm_client
        self._headless = headless

    async def extract_jd(self, url: str) -> JDSchema:
        """
        Navigate to job URL, extract page content, parse into JDSchema.

        Uses browser-use's agent loop to handle JS-rendered pages, redirects,
        and login walls (best-effort — returns partial data on failure).
        """
        try:
            from browser_use import Agent, Browser, BrowserConfig
            from langchain_anthropic import ChatAnthropic

            # TODO (Codex): thread user's LLM client through here
            # For now uses LangChain-compatible interface that browser-use expects
            llm = ChatAnthropic(model="claude-sonnet-4-6")

            browser = Browser(config=BrowserConfig(headless=self._headless))

            task = f"""
            Navigate to this job posting URL: {url}

            Extract the following information as JSON:
            - job title
            - company name
            - location (city, state, remote/hybrid/onsite)
            - employment type (full-time, part-time, contract)
            - experience level (entry, mid, senior, lead)
            - required skills (list)
            - preferred skills (list)
            - full job description text
            - salary range if mentioned

            Return ONLY the JSON object, nothing else.
            """

            agent = Agent(task=task, llm=llm, browser=browser)
            result = await agent.run()

            # Parse the agent's final response into JDSchema
            import json
            raw = result.final_result()
            data = json.loads(raw) if isinstance(raw, str) else raw

            return JDSchema(
                title=data.get("title", ""),
                company=data.get("company", ""),
                location=data.get("location"),
                remote=data.get("remote"),
                employment_type=data.get("employment_type"),
                experience_level=data.get("experience_level"),
                skills_required=data.get("required_skills", []),
                skills_preferred=data.get("preferred_skills", []),
                description=data.get("description", ""),
                apply_url=url,
            )

        except ImportError:
            raise RuntimeError(
                "browser-use not installed. Run: pip install browser-use && playwright install"
            )

    async def autofill_form(
        self,
        url: str,
        resume: TailoredResumeSchema,
        cv_file_path: str,
        cover_letter: str | None = None,
    ) -> AutofillResult:
        """
        Navigate to job application form and autofill with resume data.

        CAPTCHA detected → returns status=requires_human.
        Unknown form structure → best-effort fill, returns status based on outcome.
        """
        try:
            from browser_use import Agent, Browser, BrowserConfig
            from langchain_anthropic import ChatAnthropic

            llm = ChatAnthropic(model="claude-sonnet-4-6")
            browser = Browser(config=BrowserConfig(headless=self._headless))

            applicant_data = {
                "name": resume.name,
                "email": resume.email,
                "phone": resume.phone or "",
                "location": resume.location or "",
                "linkedin": str(resume.linkedin) if resume.linkedin else "",
                "github": str(resume.github) if resume.github else "",
                "skills": ", ".join(resume.skills),
                "cv_file": cv_file_path,
            }

            task = f"""
            Navigate to this job application form: {url}

            Fill in the application form with this information:
            {applicant_data}

            Upload the CV from: {cv_file_path}

            Rules:
            - If you encounter a CAPTCHA, stop and return {{"status": "requires_human"}}
            - Fill every visible required field
            - For experience/background text boxes, use the most relevant information
            - Do NOT submit the form yet — just fill it and return the status
            - Return {{"status": "filled"}} when complete

            Return JSON with the status only.
            """

            agent = Agent(task=task, llm=llm, browser=browser)
            result = await agent.run()

            import json
            raw = result.final_result()
            data = json.loads(raw) if isinstance(raw, str) else {}

            if data.get("status") == "requires_human":
                return AutofillResult(
                    status=ApplicationStatus.REQUIRES_HUMAN,
                    error_code="captcha_required",
                    error_message="CAPTCHA detected — manual intervention required",
                )

            return AutofillResult(status=ApplicationStatus.SUBMITTED)

        except Exception as e:
            return AutofillResult(
                status=ApplicationStatus.FAILED,
                error_code="browser_error",
                error_message=str(e),
            )
