"""JD extraction service — uses browser-use agent under the hood."""

from __future__ import annotations

from agents.browser_agent import BrowserAgent
from models.job import JDSchema


class JDExtractorService:
    def __init__(self, browser_agent: BrowserAgent | None = None) -> None:
        self._browser = browser_agent or BrowserAgent()

    async def extract(self, url: str) -> JDSchema:
        return await self._browser.extract_jd(url)
