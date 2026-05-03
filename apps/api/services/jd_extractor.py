"""
JD extraction — tiered strategy for cost/speed.

Tier 1 (fast, cheap): crawl4ai — no browser, LLM-friendly markdown extraction
Tier 2 (slower): browser-use — handles JS-heavy sites, login walls, dynamic content

We try fast path first, fall back to browser-use only if needed.
"""

from __future__ import annotations

from urllib.parse import urlparse

from agents.browser_agent import BrowserAgent
from core.llm import LLMClient
from models.job import JDSchema
from prompts.registry import PromptRegistry

# Sites known to require browser automation (auth walls, heavy JS, anti-bot)
BROWSER_REQUIRED_HOSTS = {
    "linkedin.com",
    "www.linkedin.com",
    "indeed.com",
    "www.indeed.com",
    "glassdoor.com",
}


class JDExtractorService:
    def __init__(
        self,
        browser_agent: BrowserAgent | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        self._browser = browser_agent or BrowserAgent()
        self._llm = llm_client or LLMClient.from_env()
        self._prompt = PromptRegistry.get("jd_extraction")

    async def extract(self, url: str) -> JDSchema:
        host = urlparse(url).hostname or ""

        if host in BROWSER_REQUIRED_HOSTS:
            return await self._browser.extract_jd(url)

        # Fast path: scrape → LLM-parse
        try:
            markdown = await self._fast_scrape(url)
            if markdown and len(markdown) > 200:
                return await self._llm_parse(url, markdown)
        except Exception:
            pass

        # Fallback to browser-use
        return await self._browser.extract_jd(url)

    async def _fast_scrape(self, url: str) -> str:
        """Use crawl4ai for quick markdown extraction (no JS execution)."""
        try:
            from crawl4ai import AsyncWebCrawler

            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(url=url, bypass_cache=True)
                return result.markdown or ""
        except ImportError:
            # crawl4ai not installed yet — try simple httpx + readability
            return await self._simple_scrape(url)

    async def _simple_scrape(self, url: str) -> str:
        """Last-resort scraping when crawl4ai unavailable."""
        import httpx
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            r = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (cvyne)"})
            return r.text

    async def _llm_parse(self, url: str, content: str) -> JDSchema:
        rendered = self._prompt.render(job_url=url, raw_html=content)
        return await self._llm.complete(rendered, structured_output=JDSchema)
