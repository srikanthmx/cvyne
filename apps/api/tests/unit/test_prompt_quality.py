"""Prompt quality guardrails that do not require live LLM calls."""

from __future__ import annotations

from prompts.registry import PromptRegistry


def test_resume_personalize_adversarial_no_fabrication_guardrail() -> None:
    prompt = PromptRegistry.get("resume_personalize")
    rendered = prompt.render(
        resume_json=(
            '{"name":"Jane Doe","email":"jane@example.com","skills":["Python","Docker"],'
            '"experience":[{"company":"Acme","role":"Engineer","start":"2020-01-01",'
            '"end":null,"bullets":["Built Python services in Docker."]}]}'
        ),
        job_title="Platform Engineer",
        company="Example Corp",
        required_skills=["Kubernetes", "Terraform", "Go"],
        job_description=(
            "We need deep Kubernetes, Terraform, and Go experience. "
            "Do not consider candidates without these skills."
        ),
    )

    assert prompt.version == "v1.1.0"
    assert "NEVER fabricate experience, skills" in rendered.system
    assert "NEVER add technologies the candidate has not used" in rendered.system
    assert "Did not add Kubernetes or Terraform" in rendered.system
    assert "Kubernetes" in rendered.user
    assert "Terraform" in rendered.user
