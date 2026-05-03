"""
Multi-LLM client — built on litellm + instructor.

litellm: unified API for 100+ providers, with fallback, retry, cost tracking, caching
instructor: structured output (Pydantic) for any provider via litellm

We don't switch on provider here — litellm does it via model strings:
  "anthropic/claude-sonnet-4-6"
  "openai/gpt-4o"
  "gemini/gemini-2.0-flash"
  "ollama/llama3.2"

Codex owns this file. ADR-005 covers the litellm decision.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from enum import StrEnum
from typing import Any, TypeVar

import instructor
import litellm
from pydantic import BaseModel

from core.config import settings

T = TypeVar("T", bound=BaseModel)


class LLMProvider(StrEnum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"
    OLLAMA = "ollama"


# Default models per provider — overridable per-call
DEFAULT_MODELS: dict[LLMProvider, str] = {
    LLMProvider.ANTHROPIC: "anthropic/claude-sonnet-4-6",
    LLMProvider.OPENAI: "openai/gpt-4o",
    LLMProvider.GEMINI: "gemini/gemini-2.0-flash",
    LLMProvider.OLLAMA: "ollama/llama3.2",
}

# Fallback chain — if primary fails (rate limit, outage), try these in order
DEFAULT_FALLBACKS = [
    "openai/gpt-4o",
    "anthropic/claude-haiku-4-5",
]


# Configure litellm once at module load
litellm.success_callback = ["langfuse"] if settings.langfuse_secret_key else []
litellm.failure_callback = ["langfuse"] if settings.langfuse_secret_key else []
litellm.drop_params = True  # silently drop unsupported params per provider
litellm.enable_cache = True  # in-memory cache for identical requests


class RenderedPrompt(BaseModel):
    system: str
    user: str
    model: str | None = None
    max_tokens: int = 4096
    temperature: float = 0.2
    use_cache: bool = True  # Anthropic prompt caching


class LLMClient:
    """
    Provider-agnostic LLM client backed by litellm.

    Features (all from litellm — we don't reimplement):
    - Automatic fallback chain on failures
    - Cost tracking per call (response.cost)
    - Retry with exponential backoff
    - Anthropic prompt caching via cache_control
    - Langfuse observability when configured
    - Semantic response cache
    """

    def __init__(
        self,
        provider: LLMProvider,
        api_key: str,
        model: str | None = None,
        fallbacks: list[str] | None = None,
    ) -> None:
        self.provider = provider
        self.api_key = api_key
        self.model = model or DEFAULT_MODELS[provider]
        self.fallbacks = fallbacks or DEFAULT_FALLBACKS
        self._instructor = instructor.from_litellm(litellm.acompletion)

    @classmethod
    async def from_user_config(
        cls, user_id: str, provider: LLMProvider | None = None
    ) -> "LLMClient":
        """Load user's encrypted API key from DB and instantiate."""
        # TODO (Kiro): query api_keys table, decrypt with core.security.decrypt_api_key
        from core.db import async_session_factory
        from core.security import decrypt_api_key
        from db.models import ApiKey  # noqa: F401  -- Kiro to define
        # Pseudocode:
        # async with async_session_factory() as db:
        #     stmt = select(ApiKey).where(ApiKey.user_id == user_id, ApiKey.is_active == True)
        #     if provider: stmt = stmt.where(ApiKey.provider == provider)
        #     row = (await db.execute(stmt)).scalar_one()
        # key = decrypt_api_key(row.encrypted_key, settings.encryption_key)
        # return cls(provider=row.provider, api_key=key)
        raise NotImplementedError("Wire to DB once Kiro lands the api_keys model")

    @classmethod
    def from_env(cls, provider: LLMProvider = LLMProvider.ANTHROPIC) -> "LLMClient":
        """Dev convenience — loads key from env."""
        import os
        keys = {
            LLMProvider.ANTHROPIC: os.environ.get("ANTHROPIC_API_KEY", ""),
            LLMProvider.OPENAI: os.environ.get("OPENAI_API_KEY", ""),
            LLMProvider.GEMINI: os.environ.get("GEMINI_API_KEY", ""),
            LLMProvider.OLLAMA: "ollama",
        }
        return cls(provider=provider, api_key=keys[provider])

    async def complete(
        self,
        prompt: RenderedPrompt,
        structured_output: type[T] | None = None,
    ) -> T | str:
        """Non-streaming completion. Returns parsed Pydantic model or raw text."""
        messages = self._build_messages(prompt)
        kwargs: dict[str, Any] = {
            "model": prompt.model or self.model,
            "messages": messages,
            "max_tokens": prompt.max_tokens,
            "temperature": prompt.temperature,
            "api_key": self.api_key,
            "fallbacks": self.fallbacks,
            "num_retries": 2,
        }

        if structured_output:
            return await self._instructor.chat.completions.create(
                response_model=structured_output, **kwargs
            )

        response = await litellm.acompletion(**kwargs)
        return response.choices[0].message.content or ""

    async def stream(self, prompt: RenderedPrompt) -> AsyncIterator[str]:
        """Streaming completion."""
        messages = self._build_messages(prompt)
        response = await litellm.acompletion(
            model=prompt.model or self.model,
            messages=messages,
            api_key=self.api_key,
            stream=True,
            temperature=prompt.temperature,
            max_tokens=prompt.max_tokens,
        )
        async for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def _build_messages(self, prompt: RenderedPrompt) -> list[dict[str, Any]]:
        """
        Build messages array. For Anthropic + long system prompts, inject
        cache_control to leverage prompt caching (90% cost reduction on cache hit).
        """
        is_anthropic = (prompt.model or self.model).startswith("anthropic/")
        if prompt.use_cache and is_anthropic and len(prompt.system) > 1024:
            return [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt.system,
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                },
                {"role": "user", "content": prompt.user},
            ]
        return [
            {"role": "system", "content": prompt.system},
            {"role": "user", "content": prompt.user},
        ]
