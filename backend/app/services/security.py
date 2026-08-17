"""
app/services/security.py
~~~~~~~~~~~~~~~~~~~~~~~~~
Password hashing (Argon2 via pwdlib) and JWT access token utilities.

Requires these settings (app.database.config.Settings) to be configured
via environment variables / .env:
    JWT_SECRET_KEY               (required, no default)
    JWT_ALGORITHM                 (default: "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES     (default: 30)
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.database.config import settings

password_hash = PasswordHash((Argon2Hasher(),))


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2."""
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its Argon2 hash."""
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token embedding the given claims."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)