"""
Prompt Registry — versioned, cached, observable prompts.

All prompts live here. No inline prompt strings in service files.
Codex owns this file. ADR required before structural changes.

Usage:
    prompt = PromptRegistry.get("jd_extraction")
    rendered = prompt.render(job_url="...", raw_html="...")
    result = await llm_client.complete(rendered, structured_output=JDSchema)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from jinja2 import Environment, StrictUndefined

from core.llm import LLMProvider, RenderedPrompt


@dataclass
class PromptTemplate:
    """A versioned, renderable prompt template."""

    name: str
    version: str
    system_template: str
    user_template: str
    default_model: str = "claude-sonnet-4-6"
    default_provider: LLMProvider = LLMProvider.ANTHROPIC
    max_tokens: int = 4096
    temperature: float = 0.2
    use_cache: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    _jinja_env: Environment = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._jinja_env = Environment(undefined=StrictUndefined, autoescape=False)

    def render(self, **kwargs: Any) -> RenderedPrompt:
        system = self._jinja_env.from_string(self.system_template).render(**kwargs)
        user = self._jinja_env.from_string(self.user_template).render(**kwargs)
        return RenderedPrompt(
            system=system,
            user=user,
            model=self.default_model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            use_cache=self.use_cache,
        )

    @property
    def fingerprint(self) -> str:
        """SHA-256 of system+user templates — used for change detection."""
        content = self.system_template + self.user_template
        return hashlib.sha256(content.encode()).hexdigest()[:12]


class PromptRegistry:
    """Central registry for all prompt templates."""

    _registry: dict[str, dict[str, PromptTemplate]] = {}

    @classmethod
    def register(cls, prompt: PromptTemplate) -> None:
        if prompt.name not in cls._registry:
            cls._registry[prompt.name] = {}
        cls._registry[prompt.name][prompt.version] = prompt

    @classmethod
    def get(cls, name: str, version: str = "latest") -> PromptTemplate:
        if name not in cls._registry:
            raise KeyError(f"Prompt '{name}' not found. Available: {list(cls._registry.keys())}")
        versions = cls._registry[name]
        if version == "latest":
            return sorted(versions.values(), key=lambda p: p.version)[-1]
        if version not in versions:
            raise KeyError(f"Prompt '{name}' version '{version}' not found")
        return versions[version]

    @classmethod
    def list_prompts(cls) -> list[dict[str, str]]:
        return [
            {"name": name, "versions": list(versions.keys())}
            for name, versions in cls._registry.items()
        ]


# ── Auto-register all templates on import ─────────────────────────────────────

def _load_templates() -> None:
    """Import all template modules to trigger their @register decorators."""
    from prompts.templates import (  # noqa: F401
        ats_optimizer,
        cover_letter,
        jd_extraction,
        resume_personalizer,
    )


_load_templates()
