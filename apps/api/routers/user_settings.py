"""User settings router — API key management."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from core.llm import LLMProvider

router = APIRouter()


class ApiKeyRequest(BaseModel):
    provider: LLMProvider
    api_key: str


class ApiKeyResponse(BaseModel):
    provider: LLMProvider
    is_active: bool
    masked_key: str


@router.post("/api-keys", response_model=ApiKeyResponse)
async def save_api_key(body: ApiKeyRequest) -> ApiKeyResponse:
    """Encrypt and persist a user's API key."""
    # TODO (Kiro): encrypt key with AES-256-GCM using ENCRYPTION_KEY from settings
    # TODO (Kiro): persist to api_keys table, upsert by (user_id, provider)
    masked = body.api_key[:4] + "..." + body.api_key[-4:]
    return ApiKeyResponse(provider=body.provider, is_active=True, masked_key=masked)


@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys() -> list[ApiKeyResponse]:
    """List configured providers (keys masked)."""
    # TODO (Kiro): query api_keys table for current user
    return []


@router.delete("/api-keys/{provider}")
async def delete_api_key(provider: LLMProvider) -> dict[str, str]:
    # TODO (Kiro): soft-delete or deactivate
    return {"status": "deleted"}
