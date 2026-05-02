"""
Multi-LLM adapter — the ONLY place LLM SDKs are imported.

All services and agents use LLMClient. Never import anthropic/openai/etc directly elsewhere.
Codex owns this file. ADR required before structural changes.
"""

from __future__ import annotations

import json
from enum import StrEnum
from typing import Any, AsyncIterator, TypeVar

from pydantic import BaseModel

from core.config import settings

T = TypeVar("T", bound=BaseModel)


class LLMProvider(StrEnum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"
    OLLAMA = "ollama"


class RenderedPrompt(BaseModel):
    system: str
    messages: list[dict[str, Any]]
    model: str
    max_tokens: int = 4096
    temperature: float = 0.2
    use_cache: bool = True  # inject cache_control for Anthropic when True


class LLMClient:
    """Provider-agnostic LLM client. Supports structured output and streaming."""

    def __init__(self, provider: LLMProvider, api_key: str, model: str | None = None) -> None:
        self.provider = provider
        self.api_key = api_key
        self.default_model = model or self._default_model(provider)

    @classmethod
    def from_user_config(cls, user_id: str, provider: LLMProvider | None = None) -> "LLMClient":
        """Load user's saved API key from DB. Falls back to env vars for dev."""
        # TODO (Codex): query ApiKey table, decrypt key, instantiate
        # For now, raise NotImplementedError to surface missing impl clearly
        raise NotImplementedError("Implement: query DB for user's encrypted API key")

    @classmethod
    def from_env(cls, provider: LLMProvider = LLMProvider.ANTHROPIC) -> "LLMClient":
        """Dev convenience: load API key from environment (not for production)."""
        import os
        key_map = {
            LLMProvider.ANTHROPIC: os.environ.get("ANTHROPIC_API_KEY", ""),
            LLMProvider.OPENAI: os.environ.get("OPENAI_API_KEY", ""),
            LLMProvider.GEMINI: os.environ.get("GEMINI_API_KEY", ""),
            LLMProvider.OLLAMA: "ollama",  # no key needed
        }
        return cls(provider=provider, api_key=key_map[provider])

    async def complete(
        self,
        prompt: RenderedPrompt,
        structured_output: type[T] | None = None,
    ) -> T | str:
        """Non-streaming completion. Returns parsed model or raw string."""
        match self.provider:
            case LLMProvider.ANTHROPIC:
                return await self._anthropic_complete(prompt, structured_output)
            case LLMProvider.OPENAI:
                return await self._openai_complete(prompt, structured_output)
            case LLMProvider.GEMINI:
                return await self._gemini_complete(prompt, structured_output)
            case LLMProvider.OLLAMA:
                return await self._ollama_complete(prompt, structured_output)

    async def stream(self, prompt: RenderedPrompt) -> AsyncIterator[str]:
        """Streaming completion — yields text deltas."""
        match self.provider:
            case LLMProvider.ANTHROPIC:
                async for chunk in self._anthropic_stream(prompt):
                    yield chunk
            case LLMProvider.OPENAI:
                async for chunk in self._openai_stream(prompt):
                    yield chunk
            case _:
                raise NotImplementedError(f"Streaming not yet implemented for {self.provider}")

    # ── Anthropic ─────────────────────────────────────────────────────────────

    async def _anthropic_complete(
        self, prompt: RenderedPrompt, structured_output: type[T] | None
    ) -> T | str:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=self.api_key)

        system_content: Any = prompt.system
        if prompt.use_cache and len(prompt.system) > 1024:
            # Prompt caching — reduces cost for repeated system prompts
            system_content = [
                {"type": "text", "text": prompt.system, "cache_control": {"type": "ephemeral"}}
            ]

        kwargs: dict[str, Any] = {
            "model": prompt.model or self.default_model,
            "max_tokens": prompt.max_tokens,
            "temperature": prompt.temperature,
            "system": system_content,
            "messages": prompt.messages,
        }

        if structured_output:
            kwargs["tools"] = [self._pydantic_to_anthropic_tool(structured_output)]
            kwargs["tool_choice"] = {"type": "tool", "name": structured_output.__name__}

        response = await client.messages.create(**kwargs)

        if structured_output and response.stop_reason == "tool_use":
            tool_block = next(b for b in response.content if b.type == "tool_use")
            return structured_output.model_validate(tool_block.input)

        text_block = next(b for b in response.content if b.type == "text")
        return text_block.text

    async def _anthropic_stream(self, prompt: RenderedPrompt) -> AsyncIterator[str]:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=self.api_key)
        async with client.messages.stream(
            model=prompt.model or self.default_model,
            max_tokens=prompt.max_tokens,
            system=prompt.system,
            messages=prompt.messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    # ── OpenAI ────────────────────────────────────────────────────────────────

    async def _openai_complete(
        self, prompt: RenderedPrompt, structured_output: type[T] | None
    ) -> T | str:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key)
        messages = [{"role": "system", "content": prompt.system}, *prompt.messages]

        if structured_output:
            response = await client.beta.chat.completions.parse(
                model=prompt.model or self.default_model,
                messages=messages,
                response_format=structured_output,
                temperature=prompt.temperature,
            )
            return response.choices[0].message.parsed  # type: ignore[return-value]

        response = await client.chat.completions.create(
            model=prompt.model or self.default_model,
            messages=messages,
            temperature=prompt.temperature,
            max_tokens=prompt.max_tokens,
        )
        return response.choices[0].message.content or ""

    async def _openai_stream(self, prompt: RenderedPrompt) -> AsyncIterator[str]:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key)
        messages = [{"role": "system", "content": prompt.system}, *prompt.messages]
        stream = await client.chat.completions.create(
            model=prompt.model or self.default_model,
            messages=messages,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    # ── Gemini ────────────────────────────────────────────────────────────────

    async def _gemini_complete(
        self, prompt: RenderedPrompt, structured_output: type[T] | None
    ) -> T | str:
        # TODO (Codex): implement Gemini via google-generativeai SDK
        raise NotImplementedError("Gemini adapter not yet implemented")

    # ── Ollama ────────────────────────────────────────────────────────────────

    async def _ollama_complete(
        self, prompt: RenderedPrompt, structured_output: type[T] | None
    ) -> T | str:
        # TODO (Codex): implement Ollama via ollama SDK
        raise NotImplementedError("Ollama adapter not yet implemented")

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _default_model(provider: LLMProvider) -> str:
        return {
            LLMProvider.ANTHROPIC: "claude-sonnet-4-6",
            LLMProvider.OPENAI: "gpt-4o",
            LLMProvider.GEMINI: "gemini-2.0-flash",
            LLMProvider.OLLAMA: "llama3.2",
        }[provider]

    @staticmethod
    def _pydantic_to_anthropic_tool(model: type[BaseModel]) -> dict[str, Any]:
        schema = model.model_json_schema()
        return {
            "name": model.__name__,
            "description": model.__doc__ or f"Extract {model.__name__}",
            "input_schema": schema,
        }
