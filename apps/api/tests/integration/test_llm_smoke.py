"""Integration smoke tests for LiteLLM + instructor + prompt registry."""

from __future__ import annotations

import os

import pytest

from core.llm import LLMClient, LLMProvider
from models.job import JDSchema
from prompts.registry import PromptRegistry

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY is required for real LLM integration tests",
)


def _response_cost(hidden_params: dict) -> float:
    return float(hidden_params.get("response_cost") or 0)


def _cache_hit_tokens(hidden_params: dict) -> int:
    candidates = [
        "prompt_cache_hit_tokens",
        "cache_read_input_tokens",
        "cache_hit_input_tokens",
    ]
    return sum(int(hidden_params.get(key) or 0) for key in candidates)


@pytest.mark.asyncio
async def test_anthropic_structured_output() -> None:
    client = LLMClient.from_env(LLMProvider.ANTHROPIC)
    prompt = PromptRegistry.get("jd_extraction")
    rendered = prompt.render(
        job_url="https://example.com/job",
        raw_html=(
            "<h1>Senior Python Engineer at Acme Corp</h1>"
            "<p>5+ years Python, FastAPI, AWS required</p>"
        ),
    )

    result = await client.complete(rendered, structured_output=JDSchema)

    assert result.title.lower().startswith("senior python")
    assert result.company == "Acme Corp"
    assert "python" in [s.lower() for s in result.skills_required]
    assert _response_cost(client.last_hidden_params) > 0


@pytest.mark.asyncio
async def test_anthropic_prompt_cache_hits_on_repeated_prompt() -> None:
    client = LLMClient.from_env(LLMProvider.ANTHROPIC)
    prompt = PromptRegistry.get("resume_personalize")
    rendered = prompt.render(
        resume_json=(
            '{"name":"Jane Doe","email":"jane@example.com",'
            '"skills":["Python","FastAPI"],"experience":[]}'
        ),
        job_title="Senior Python Engineer",
        company="Acme Corp",
        required_skills=["Python", "FastAPI", "AWS"],
        job_description="Build APIs with Python and FastAPI on AWS.",
    )
    rendered.max_tokens = 64

    await client.complete(rendered)
    assert _response_cost(client.last_hidden_params) > 0

    await client.complete(rendered)

    # Anthropic reports prompt cache reads through LiteLLM response metadata;
    # the second identical call should reuse the cached system block.
    assert _response_cost(client.last_hidden_params) > 0
    assert _cache_hit_tokens(client.last_hidden_params) > 0
