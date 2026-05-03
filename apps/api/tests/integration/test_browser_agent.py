"""Integration tests for browser-use-backed job extraction."""

from __future__ import annotations

import os

import pytest

from agents.browser_agent import BrowserAgent
from core.llm import LLMProvider

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY is required for browser-use integration tests",
)


@pytest.mark.asyncio
async def test_extract_jd_from_real_url() -> None:
    agent = BrowserAgent(provider=LLMProvider.ANTHROPIC, headless=True)

    # Anthropic's Lever board is stable and public; if it begins blocking automation,
    # replace with another public job board URL and document the reason here.
    jd = await agent.extract_jd("https://jobs.lever.co/anthropic")

    assert jd.title
    assert jd.company
