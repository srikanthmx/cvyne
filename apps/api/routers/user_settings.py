"""User settings router — API key management."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.db import get_session
from core.llm import LLMProvider
from core.security import decrypt_api_key, encrypt_api_key
from db.models import ApiKey

router = APIRouter()

# Placeholder user_id until Clerk auth is wired
_PLACEHOLDER_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class ApiKeyRequest(BaseModel):
    provider: LLMProvider
    api_key: str


class ApiKeyResponse(BaseModel):
    provider: LLMProvider
    is_active: bool
    masked_key: str


@router.post("/api-keys", response_model=ApiKeyResponse)
async def save_api_key(
    body: ApiKeyRequest,
    db: AsyncSession = Depends(get_session),
) -> ApiKeyResponse:
    """Encrypt and persist a user's API key. Upserts by (user_id, provider)."""
    encrypted = encrypt_api_key(body.api_key, settings.encryption_key)

    # Upsert: deactivate existing key for this provider, insert new one
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.user_id == _PLACEHOLDER_USER_ID,
            ApiKey.provider == body.provider.value,
            ApiKey.is_active == True,  # noqa: E712
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.is_active = False

    new_key = ApiKey(
        user_id=_PLACEHOLDER_USER_ID,
        provider=body.provider.value,
        encrypted_key=encrypted,
        is_active=True,
    )
    db.add(new_key)
    await db.flush()

    masked = body.api_key[:4] + "..." + body.api_key[-4:]
    return ApiKeyResponse(provider=body.provider, is_active=True, masked_key=masked)


@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    db: AsyncSession = Depends(get_session),
) -> list[ApiKeyResponse]:
    """List configured providers (keys masked)."""
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.user_id == _PLACEHOLDER_USER_ID,
            ApiKey.is_active == True,  # noqa: E712
        )
    )
    rows = result.scalars().all()
    out = []
    for row in rows:
        try:
            plaintext = decrypt_api_key(row.encrypted_key, settings.encryption_key)
            masked = plaintext[:4] + "..." + plaintext[-4:] if len(plaintext) > 8 else "****"
        except Exception:
            masked = "****"
        out.append(ApiKeyResponse(provider=row.provider, is_active=row.is_active, masked_key=masked))
    return out


@router.delete("/api-keys/{provider}")
async def delete_api_key(
    provider: LLMProvider,
    db: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.user_id == _PLACEHOLDER_USER_ID,
            ApiKey.provider == provider.value,
            ApiKey.is_active == True,  # noqa: E712
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="API key not found")
    row.is_active = False
    return {"status": "deleted"}
