from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import bcrypt
from jose import JWTError, jwt

from app.core.config import BASE_DIR, settings


def _get_rsa_key(key_type: str) -> Optional[str]:
    if key_type == "private" and settings.RSA_PRIVATE_KEY_PATH:
        path = Path(settings.RSA_PRIVATE_KEY_PATH)
        if path.is_file():
            return path.read_text()
    elif key_type == "public" and settings.RSA_PUBLIC_KEY_PATH:
        path = Path(settings.RSA_PUBLIC_KEY_PATH)
        if path.is_file():
            return path.read_text()
    return None


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_token(
    subject: str | Any,
    expires_delta: Optional[timedelta] = None,
    token_type: str = "access",
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {"exp": expire, "sub": str(subject), "type": token_type, "iat": datetime.now(timezone.utc), "jti": str(uuid.uuid4())}
    private_key = _get_rsa_key("private")
    if private_key:
        return jwt.encode(payload, private_key, algorithm="RS256")
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict[str, Any]:
    try:
        public_key = _get_rsa_key("public")
        if public_key:
            return jwt.decode(token, public_key, algorithms=["RS256"])
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        return {}
