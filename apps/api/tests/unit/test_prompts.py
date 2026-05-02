"""Tests for prompt registry and template rendering."""

import pytest
from prompts.registry import PromptRegistry


def test_registry_loads_all_prompts():
    prompts = PromptRegistry.list_prompts()
    names = [p["name"] for p in prompts]
    assert "jd_extraction" in names
    assert "resume_personalize" in names
    assert "ats_optimize" in names
    assert "cover_letter" in names


def test_jd_extraction_renders():
    prompt = PromptRegistry.get("jd_extraction")
    rendered = prompt.render(job_url="https://example.com/job/123", raw_html="<h1>Engineer</h1>")
    assert "https://example.com/job/123" in rendered.messages[0]["content"]
    assert len(rendered.system) > 100


def test_resume_personalize_renders():
    prompt = PromptRegistry.get("resume_personalize")
    rendered = prompt.render(
        resume_json='{"name": "Jane Doe"}',
        job_title="Software Engineer",
        company="Acme Corp",
        required_skills=["Python", "FastAPI"],
        job_description="We need a Python engineer...",
    )
    assert "Jane Doe" in rendered.messages[0]["content"]
    assert "Acme Corp" in rendered.messages[0]["content"]


def test_prompt_fingerprint_stable():
    p = PromptRegistry.get("jd_extraction")
    assert len(p.fingerprint) == 12


def test_version_resolution():
    p_latest = PromptRegistry.get("jd_extraction", version="latest")
    p_explicit = PromptRegistry.get("jd_extraction", version="v1.0.0")
    assert p_latest.fingerprint == p_explicit.fingerprint


def test_missing_prompt_raises():
    with pytest.raises(KeyError, match="nonexistent"):
        PromptRegistry.get("nonexistent")
