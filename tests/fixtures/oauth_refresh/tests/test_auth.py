"""Tests for authentication module."""

import pytest
from datetime import timedelta
from unittest.mock import Mock, patch

from auth.token import (
    create_access_token,
    create_refresh_token,
    decode_token,
    validate_refresh_token,
    validate_access_token,
)
from auth.endpoints import refresh_token


def test_create_access_token():
    """Test access token creation."""
    token = create_access_token({"sub": "testuser", "user_id": 1})
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_refresh_token():
    """Test refresh token creation."""
    token = create_refresh_token({"sub": "testuser", "user_id": 1})
    assert token is not None
    assert isinstance(token, str)


def test_decode_valid_token():
    """Test decoding a valid token."""
    token = create_access_token({"sub": "testuser", "user_id": 1})
    payload = decode_token(token)
    assert payload["sub"] == "testuser"
    assert payload["user_id"] == 1
    assert payload["type"] == "access"


def test_decode_expired_token():
    """Test decoding an expired token."""
    from auth.token import JWT_SECRET, JWT_ALGORITHM
    import jwt
    from datetime import datetime, timezone

    expired_token = jwt.encode(
        {"sub": "testuser", "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )

    with pytest.raises(Exception) as exc_info:
        decode_token(expired_token)
    assert "expired" in str(exc_info.value).lower()


def test_validate_refresh_token():
    """Test refresh token validation."""
    token = create_refresh_token({"sub": "testuser", "user_id": 1})
    payload = validate_refresh_token(token)
    assert payload["type"] == "refresh"


def test_validate_access_token():
    """Test access token validation."""
    token = create_access_token({"sub": "testuser", "user_id": 1})
    payload = validate_access_token(token)
    assert payload["type"] == "access"


def test_validate_wrong_token_type():
    """Test validation fails for wrong token type."""
    access_token = create_access_token({"sub": "testuser", "user_id": 1})
    with pytest.raises(Exception) as exc_info:
        validate_refresh_token(access_token)
    assert "Invalid token type" in str(exc_info.value)


@pytest.mark.asyncio
async def test_refresh_endpoint_success():
    """Test successful token refresh."""
    # Mock database and request
    mock_db = Mock()
    mock_user = Mock()
    mock_user.id = 1
    mock_user.username = "testuser"
    mock_user.is_active = True
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    mock_request = Mock()
    mock_request.json.return_value = {"refresh_token": create_refresh_token({"sub": "testuser", "user_id": 1})}

    with patch("auth.endpoints.blacklist_token"), \
         patch("auth.endpoints.is_token_blacklisted", return_value=False):
        result = await refresh_token(mock_request, mock_db)

    assert "access_token" in result
    assert "refresh_token" in result
    assert result["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_endpoint_missing_token():
    """Test refresh with missing token."""
    mock_db = Mock()
    mock_request = Mock()
    mock_request.json.return_value = {}

    with pytest.raises(Exception) as exc_info:
        await refresh_token(mock_request, mock_db)

    assert "Refresh token required" in str(exc_info.value)


@pytest.mark.asyncio
async def test_refresh_endpoint_blacklisted():
    """Test refresh with blacklisted token."""
    mock_db = Mock()
    mock_request = Mock()
    mock_request.json.return_value = {"refresh_token": create_refresh_token({"sub": "testuser", "user_id": 1})}

    with patch("auth.endpoints.is_token_blacklisted", return_value=True):
        with pytest.raises(Exception) as exc_info:
            await refresh_token(mock_request, mock_db)

    assert "revoked" in str(exc_info.value).lower()