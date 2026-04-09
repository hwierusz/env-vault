"""Encryption and decryption utilities for env-vault using Fernet symmetric encryption."""

import os
import base64
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


SALT_LENGTH = 16
ITERATIONS = 480_000


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a Fernet-compatible key from a password and salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def generate_salt() -> bytes:
    """Generate a cryptographically secure random salt."""
    return os.urandom(SALT_LENGTH)


def encrypt(plaintext: str, password: str) -> bytes:
    """Encrypt plaintext using a password-derived key.

    Returns salt + encrypted data as a single bytes object.
    """
    salt = generate_salt()
    key = derive_key(password, salt)
    token = Fernet(key).encrypt(plaintext.encode())
    return salt + token


def decrypt(data: bytes, password: str) -> str:
    """Decrypt data using a password-derived key.

    Expects data in the format produced by `encrypt`.
    Raises ValueError on wrong password or corrupted data.
    """
    salt = data[:SALT_LENGTH]
    token = data[SALT_LENGTH:]
    key = derive_key(password, salt)
    try:
        return Fernet(key).decrypt(token).decode()
    except (InvalidToken, Exception) as exc:
        raise ValueError("Decryption failed: invalid password or corrupted data.") from exc
