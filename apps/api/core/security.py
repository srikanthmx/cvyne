"""AES-256-GCM encryption for user API keys."""

from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def encrypt_api_key(plaintext: str, key_hex: str) -> str:
    """Encrypt a plaintext API key. Returns base64-encoded nonce+ciphertext."""
    key = bytes.fromhex(key_hex)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ct).decode()


def decrypt_api_key(ciphertext_b64: str, key_hex: str) -> str:
    """Decrypt a base64-encoded nonce+ciphertext. Returns plaintext API key."""
    key = bytes.fromhex(key_hex)
    aesgcm = AESGCM(key)
    data = base64.b64decode(ciphertext_b64)
    nonce, ct = data[:12], data[12:]
    return aesgcm.decrypt(nonce, ct, None).decode()
