"""
Browser Agent — wraps browser-use for JD extraction and form autofill.

Repo: https://github.com/browser-use/browser-use
Install: uv add browser-use && uv sync
Requires Python >= 3.11

browser-use ships its own LLM clients — DO NOT use LangChain wrappers.
- ChatBrowserUse() — optimized default
- ChatAnthropic(model='claude-sonnet-4-6')
- ChatGoogle(model='gemini-3-flash-preview')
- ChatOpenAI(model='gpt-4o') (via browser_use.llm)

Codex owns this file.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from core.llm import LLMProvider
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
    Stateless browser automation agent built on browser-use.

    Each method spins up a fresh Browser context — no shared state.
    """

    def __init__(
        self,
        provider: LLMProvider = LLMProvider.ANTHROPIC,
        api_key: str | None = None,
        model: str | None = None,
        headless: bool = True,
        application_id: str | None = None,
        redis_url: str | None = None,
    ) -> None:
        self._provider = provider
        self._api_key = api_key
        self._model = model
        self._headless = headless
        # When application_id + redis_url are set, the agent publishes per-step
        # screenshots to the channel app:{application_id} so the frontend can
        # render a live "agent's-eye view" of what the browser is doing.
        self._application_id = application_id
        self._redis_url = redis_url

    def _build_step_screenshot_callback(self):
        """
        Hook into browser-use's per-step callback to publish screenshots.
        Returns None when there's no application_id — agent runs normally.
        """
        if not (self._application_id and self._redis_url):
            return None

        import json
        import redis.asyncio as aioredis

        channel = f"app:{self._application_id}"
        redis_url = self._redis_url

        async def on_step(state, agent_output, step_num):
            screenshot_b64 = getattr(state, "screenshot", None)
            if not screenshot_b64:
                return
            payload = {
                "application_id": str(self._application_id),
                "kind": "screenshot",
                "step": step_num,
                "screenshot_b64": screenshot_b64,
                "url": getattr(state, "url", None),
                "title": getattr(state, "title", None),
            }
            r = aioredis.from_url(redis_url)
            try:
                await r.publish(channel, json.dumps(payload))
            finally:
                await r.aclose()

        return on_step

    def _build_llm(self):
        """Build a browser-use compatible LLM client. Never use LangChain wrappers."""
        match self._provider:
            case LLMProvider.ANTHROPIC:
                from browser_use.llm import ChatAnthropic
                return ChatAnthropic(
                    model=self._model or "claude-sonnet-4-6",
                    api_key=self._api_key,
                )
            case LLMProvider.OPENAI:
                from browser_use.llm import ChatOpenAI
                return ChatOpenAI(
                    model=self._model or "gpt-4o",
                    api_key=self._api_key,
                )
            case LLMProvider.GEMINI:
                from browser_use.llm import ChatGoogle
                return ChatGoogle(
                    model=self._model or "gemini-2.0-flash",
                    api_key=self._api_key,
                )
            case _:
                # Default — browser-use's own optimized model
                from browser_use import ChatBrowserUse
                return ChatBrowserUse()

    async def extract_jd(self, url: str) -> JDSchema:
        """Navigate to job URL, extract JD into structured schema."""
        from browser_use import Agent, Browser

        browser = Browser(headless=self._headless)
        llm = self._build_llm()

        task = f"""Navigate to this job posting: {url}

Extract the following as a single JSON object (no markdown, no commentary):
{{
  "title": "string",
  "company": "string",
  "location": "string|null",
  "remote": true|false|null,
  "employment_type": "full-time|part-time|contract|null",
  "experience_level": "entry|mid|senior|lead|executive|null",
  "skills_required": ["string"],
  "skills_preferred": ["string"],
  "description": "full job description text",
  "salary_min": number|null,
  "salary_max": number|null,
  "salary_currency": "string|null"
}}

Rules:
- Extract ONLY information explicitly on the page
- Do not infer or fabricate
- Return JSON only, nothing else"""

        try:
            agent = Agent(
                task=task,
                llm=llm,
                browser=browser,
                use_vision=False,
                register_new_step_callback=self._build_step_screenshot_callback(),
            )
            history = await agent.run(max_steps=20)
            raw = history.final_result()
        finally:
            await browser.stop()

        try:
            data = json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            data = {"title": "", "company": "", "description": str(raw or "")}

        return JDSchema(
            title=data.get("title", ""),
            company=data.get("company", ""),
            location=data.get("location"),
            remote=data.get("remote"),
            employment_type=data.get("employment_type"),
            experience_level=data.get("experience_level"),
            skills_required=data.get("skills_required", []),
            skills_preferred=data.get("skills_preferred", []),
            description=data.get("description", ""),
            salary_min=data.get("salary_min"),
            salary_max=data.get("salary_max"),
            salary_currency=data.get("salary_currency"),
            apply_url=url,
        )

    async def autofill_form(
        self,
        url: str,
        resume: TailoredResumeSchema,
        cv_file_path: str,
        cover_letter: str | None = None,
        auto_submit: bool = False,
    ) -> AutofillResult:
        """
        Fill the job application form with resume data and upload CV.

        - auto_submit=False (default): fills form but does NOT submit (safer)
        - CAPTCHA detected → returns status=requires_human
        """
        from browser_use import Agent, Browser

        browser = Browser(headless=self._headless)
        llm = self._build_llm()

        applicant = {
            "first_name": resume.name.split()[0] if resume.name else "",
            "last_name": " ".join(resume.name.split()[1:]) if len(resume.name.split()) > 1 else "",
            "full_name": resume.name,
            "email": resume.email,
            "phone": resume.phone or "",
            "location": resume.location or "",
            "linkedin": str(resume.linkedin) if resume.linkedin else "",
            "github": str(resume.github) if resume.github else "",
            "portfolio": str(resume.portfolio) if resume.portfolio else "",
            "summary": resume.summary or "",
            "skills": resume.skills,
        }

        submit_clause = (
            "After all required fields are filled and CV is uploaded, click the Submit button."
            if auto_submit
            else "Do NOT submit the form. Stop after all fields are filled and CV uploaded."
        )

        cover_clause = (
            f"\n\nCover letter text to paste in any cover-letter field:\n{cover_letter}"
            if cover_letter
            else ""
        )

        task = f"""Navigate to this job application form: {url}

Applicant data (use these values exactly):
{json.dumps(applicant, indent=2)}

CV file to upload: {cv_file_path}
{cover_clause}

Instructions:
1. Fill every visible required field using the applicant data
2. Upload the CV file when prompted
3. For free-text fields ("Why do you want this role?"), use 1-2 sentences from the summary
4. If you encounter a CAPTCHA, stop immediately and return: {{"status": "requires_human", "reason": "captcha"}}
5. If a required field has no matching data, return: {{"status": "requires_human", "reason": "missing_field", "field": "field name"}}
6. {submit_clause}

Return JSON only:
{{"status": "filled" | "submitted" | "requires_human" | "failed", "reason": "string|null"}}"""

        try:
            agent = Agent(
                task=task,
                llm=llm,
                browser=browser,
                use_vision=False,
                register_new_step_callback=self._build_step_screenshot_callback(),
            )
            history = await agent.run(max_steps=35)
            raw = history.final_result()
            data = json.loads(raw) if isinstance(raw, str) else (raw or {})
        except Exception as e:
            return AutofillResult(
                status=ApplicationStatus.FAILED,
                error_code="browser_error",
                error_message=str(e),
            )
        finally:
            await browser.stop()

        status_str = data.get("status", "failed")

        if status_str == "requires_human":
            return AutofillResult(
                status=ApplicationStatus.REQUIRES_HUMAN,
                error_code=data.get("reason", "unknown"),
                error_message=data.get("reason"),
            )
        if status_str == "submitted":
            return AutofillResult(status=ApplicationStatus.SUBMITTED)
        if status_str == "filled":
            # Form filled but not submitted — still considered success in default mode
            return AutofillResult(status=ApplicationStatus.SUBMITTED)

        return AutofillResult(
            status=ApplicationStatus.FAILED,
            error_code="autofill_failed",
            error_message=data.get("reason"),
        )
