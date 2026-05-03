"""Async S3/MinIO client using aioboto3."""

from __future__ import annotations

import aioboto3

from core.config import settings

_session = aioboto3.Session()


def _client_kwargs() -> dict:
    return {
        "endpoint_url": settings.s3_endpoint,
        "aws_access_key_id": settings.s3_access_key,
        "aws_secret_access_key": settings.s3_secret_key,
        "region_name": settings.s3_region,
    }


async def upload_bytes(key: str, data: bytes, content_type: str) -> str:
    """Upload bytes to S3/MinIO. Returns the S3 key."""
    async with _session.client("s3", **_client_kwargs()) as s3:
        await s3.put_object(
            Bucket=settings.s3_bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
    return key


async def get_presigned_url(key: str, ttl: int = 3600) -> str:
    """Generate a presigned GET URL for the given key. TTL in seconds."""
    async with _session.client("s3", **_client_kwargs()) as s3:
        url: str = await s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.s3_bucket, "Key": key},
            ExpiresIn=ttl,
        )
    return url


async def ensure_bucket_exists() -> None:
    """Create the bucket if it doesn't exist (idempotent, dev helper)."""
    async with _session.client("s3", **_client_kwargs()) as s3:
        try:
            await s3.head_bucket(Bucket=settings.s3_bucket)
        except Exception:
            await s3.create_bucket(Bucket=settings.s3_bucket)
