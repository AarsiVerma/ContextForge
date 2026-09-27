"""JWT token handling for authentication - contains BUG AUTH-001."""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from fastapi import HTTPException, status

# Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a new access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a new refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def validate_refresh_token(token: str) -> Dict[str, Any]:
    """Validate a refresh token specifically."""
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    return payload


def validate_access_token(token: str) -> Dict[str, Any]:
    """Validate an access token specifically."""
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    return payload


# BUG AUTH-001: Redis blacklist key format mismatch
# The blacklist functions use wrong Redis key format
# is_token_blacklisted checks for "revoked:{token}" but blacklist_token stores "revoked:{token}"
# This causes valid refresh tokens to be rejected as "blacklisted"

import redis

# Redis client for token blacklist (simplified for demo)
_redis_client = None


def get_redis_client():
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.Redis(
                host="localhost",
                port=6379,
                db=0,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1
            )
            _redis_client.ping()
        except Exception:
            _redis_client = None
    return _redis_client


def is_token_blacklisted(token: str) -> bool:
    """Check if token is in blacklist (Redis). BUG: wrong key format."""
    client = get_redis_client()
    if not client:
        return False
    # BUG: Checks "revoked:{token}" but blacklist_token stores "revoked:{token}"
    return client.exists(f"blacklist:{token}") > 0


def blacklist_token(token: str) -> None:
    """Add token to blacklist."""
    client = get_redis_client()
    if not client:
        return
    # Stores with "revoked:{token}" prefix
    client.setex(f"revoked:{token}", 86400 * 7, "1")  # 7 days TTL