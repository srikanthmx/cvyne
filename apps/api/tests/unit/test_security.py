"""Unit tests for AES-256-GCM API key encryption."""

from __future__ import annotations

import os

import pytest

from core.security import decrypt_api_key, encrypt_api_key


def _random_key_hex() -> str:
    return os.urandom(32).hex()


def test_round_trip_basic() -> None:
    key = _random_key_hex()
    plaintext = "sk-test-1234567890abcdef"
    ciphertext = encrypt_api_key(plaintext, key)
    assert decrypt_api_key(ciphertext, key) == plaintext


def test_ciphertext_differs_from_plaintext() -> None:
    key = _random_key_hex()
    plaintext = "my-secret-key"
    ciphertext = encrypt_api_key(plaintext, key)
    assert ciphertext != plaintext


def test_different_nonces_each_call() -> None:
    """Each encryption call should produce a different ciphertext (random nonce)."""
    key = _random_key_hex()
    plaintext = "same-key"
    ct1 = encrypt_api_key(plaintext, key)
    ct2 = encrypt_api_key(plaintext, key)
    assert ct1 != ct2


def test_wrong_key_raises() -> None:
    key = _random_key_hex()
    wrong_key = _random_key_hex()
    ciphertext = encrypt_api_key("secret", key)
    with pytest.raises(Exception):
        decrypt_api_key(ciphertext, wrong_key)


def test_empty_string_round_trip() -> None:
    key = _random_key_hex()
    assert decrypt_api_key(encrypt_api_key("", key), key) == ""
