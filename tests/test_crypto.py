"""Tests for the crypto module."""

import pytest
from env_vault.crypto import encrypt, decrypt, generate_salt, derive_key, SALT_LENGTH


PASSWORD = "super-secret-password"
PLAINTEXT = "MY_API_KEY=abc123\nDB_URL=postgres://localhost/db"


def test_encrypt_returns_bytes():
    result = encrypt(PLAINTEXT, PASSWORD)
    assert isinstance(result, bytes)


def test_encrypted_length_exceeds_salt():
    result = encrypt(PLAINTEXT, PASSWORD)
    assert len(result) > SALT_LENGTH


def test_decrypt_roundtrip():
    encrypted = encrypt(PLAINTEXT, PASSWORD)
    assert decrypt(encrypted, PASSWORD) == PLAINTEXT


def test_different_encryptions_produce_different_ciphertext():
    enc1 = encrypt(PLAINTEXT, PASSWORD)
    enc2 = encrypt(PLAINTEXT, PASSWORD)
    assert enc1 != enc2  # Different salts each time


def test_decrypt_wrong_password_raises():
    encrypted = encrypt(PLAINTEXT, PASSWORD)
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt(encrypted, "wrong-password")


def test_decrypt_corrupted_data_raises():
    encrypted = bytearray(encrypt(PLAINTEXT, PASSWORD))
    encrypted[20] ^= 0xFF  # Flip bits in token area
    with pytest.raises(ValueError):
        decrypt(bytes(encrypted), PASSWORD)


def test_generate_salt_length():
    salt = generate_salt()
    assert len(salt) == SALT_LENGTH


def test_generate_salt_is_random():
    assert generate_salt() != generate_salt()


def test_derive_key_deterministic():
    salt = generate_salt()
    key1 = derive_key(PASSWORD, salt)
    key2 = derive_key(PASSWORD, salt)
    assert key1 == key2


def test_derive_key_different_salts():
    key1 = derive_key(PASSWORD, generate_salt())
    key2 = derive_key(PASSWORD, generate_salt())
    assert key1 != key2
