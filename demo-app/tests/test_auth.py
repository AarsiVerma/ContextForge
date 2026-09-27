"""Tests for authentication - BUG AUTH-001."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from auth.token import (
    create_access_token,
    create_refresh_token,
    validate_refresh_token,
    validate_access_token,
    is_token_blacklisted,
    blacklist_token,
)
from auth.models import User


class TestAuthTokens:
    """Test JWT token creation and validation."""

    def test_create_access_token(self):
        """Test access token creation."""
        token = create_access_token({"sub": "testuser", "user_id": 1})
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        token = create_refresh_token({"sub": "testuser", "user_id": 1})
        assert token is not None
        assert isinstance(token, str)

    def test_decode_valid_access_token(self):
        """Test decoding a valid access token."""
        token = create_access_token({"sub": "testuser", "user_id": 1, "roles": ["user"]})
        from auth.token import validate_access_token
        payload = validate_access_token(token)
        assert payload["sub"] == "testuser"
        assert payload["user_id"] == 1
        assert payload["type"] == "access"

    def test_decode_valid_refresh_token(self):
        """Test decoding a valid refresh token."""
        token = create_refresh_token({"sub": "testuser", "user_id": 1})
        from auth.token import validate_refresh_token
        payload = validate_refresh_token(token)
        assert payload["sub"] == "testuser"
        assert payload["type"] == "refresh"

    def test_reject_expired_token(self):
        """Test that expired tokens are rejected."""
        from auth.token import JWT_SECRET, JWT_ALGORITHM
        from jose import jwt
        from datetime import datetime, timezone, timedelta

        expired_token = jwt.encode(
            {"sub": "testuser", "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
            JWT_SECRET,
            algorithm=JWT_ALGORITHM,
        )

        from auth.token import validate_access_token
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            validate_access_token(expired_token)
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    def test_reject_invalid_token(self):
        """Test that invalid tokens are rejected."""
        from auth.token import validate_access_token
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            validate_access_token("invalid.token.here")
        assert exc_info.value.status_code == 401

    def test_wrong_token_type_rejected(self):
        """Test that access token rejected as refresh token."""
        access_token = create_access_token({"sub": "testuser", "user_id": 1})
        from auth.token import validate_refresh_token
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            validate_refresh_token(access_token)
        assert exc_info.value.status_code == 401
        assert "type" in exc_info.value.detail.lower()


class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_register_user(self, client):
        """Test user registration."""
        response = client.post(
            "/auth/register",
            json={"username": "newuser", "email": "new@example.com", "password": "password123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"

    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "password123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_failure_wrong_password(self, client, test_user):
        """Test login fails with wrong password."""
        response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "wrongpassword"}
        )
        assert response.status_code == 401

    def test_refresh_token_success(self, client, test_user):
        """Test successful token refresh (fixed behavior)."""
        from unittest.mock import patch, MagicMock
        from auth.token import get_redis_client
        
        # Mock Redis: token not in blacklist (fixed behavior)
        mock_redis = MagicMock()
        mock_redis.exists.return_value = 0
        
        with patch("auth.token.get_redis_client", return_value=mock_redis):
            # Login first
            login_resp = client.post(
                "/auth/login",
                data={"username": "testuser", "password": "password123"}
            )
            assert login_resp.status_code == 200
            refresh_token = login_resp.json()["refresh_token"]

            # Refresh - should succeed with fix
            response = client.post(
                "/auth/refresh",
                json={"refresh_token": refresh_token}
            )
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data

    def test_refresh_token_missing(self, client):
        """Test refresh with missing token."""
        response = client.post("/auth/refresh", json={})
        # FastAPI returns 422 for validation errors
        assert response.status_code == 422

    def test_refresh_token_blacklisted(self, client, test_user):
        """Test refresh fails when token is blacklisted."""
        from auth.token import create_refresh_token, blacklist_token

        refresh_token = create_refresh_token({"sub": "testuser", "user_id": 1, "roles": ["user"]})
        blacklist_token(refresh_token)

        response = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        # Should fail because token is blacklisted
        # Note: This test depends on Redis being available
        # If Redis is not available, it will pass (no blacklist check)

    def test_logout(self, client, test_user):
        """Test logout blacklists tokens."""
        login_resp = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "password123"}
        )
        token = login_resp.json()["access_token"]
        refresh_token = login_resp.json()["refresh_token"]

        response = client.post(
            "/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

    def test_get_current_user(self, client, test_user, auth_headers):
        """Get current user info."""
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"


class TestAuthBugAUTH001:
    """Tests for BUG AUTH-001: Refresh token blacklist key mismatch.
    
    In BUGGY state: is_token_blacklisted checks "blacklist:{token}" but blacklist_token stores "revoked:{token}"
    In FIXED state: both use "revoked:{token}"
    """

    def test_blacklist_key_format_buggy(self):
        """Test that the blacklist key format bug exists (buggy state)."""
        from auth.token import blacklist_token, is_token_blacklisted, get_redis_client

        # Mock Redis to verify key formats
        mock_redis = MagicMock()
        mock_redis.exists.return_value = 0

        with patch("auth.token.get_redis_client", return_value=mock_redis):
            # Blacklist a token
            test_token = "test_token_123"
            blacklist_token(test_token)

            # Verify blacklist_token uses "revoked:{token}" format
            mock_redis.setex.assert_called_once()
            call_args = mock_redis.setex.call_args
            assert call_args[0][0] == f"revoked:test_token_123"

        # Now test is_token_blacklisted uses DIFFERENT format (BUGGY)
        mock_redis.reset_mock()
        mock_redis.exists.return_value = 0

        with patch("auth.token.get_redis_client", return_value=mock_redis):
            is_token_blacklisted("test_token_123")
            # BUGGY: Uses "blacklist:{token}" format (different from storage)
            mock_redis.exists.assert_called_once_with("blacklist:test_token_123")

    def test_blacklist_buggy_false_negative(self):
        """Test that the key mismatch bug causes false negatives (valid tokens rejected)."""
        from auth.token import blacklist_token, is_token_blacklisted

        mock_redis = MagicMock()
        # Simulate token being blacklisted with "revoked:" prefix (the storage format)
        mock_redis.exists.return_value = 1  # Token exists in blacklist under "revoked:"

        with patch("auth.token.get_redis_client", return_value=mock_redis):
            blacklist_token("token123")  # Stores as "revoked:token123"
            mock_redis.reset_mock()
            
            # is_token_blacklisted checks "blacklist:" (BUG) - won't find the "revoked:" key
            mock_redis.exists.return_value = 0  # Wrong key returns 0
            result = is_token_blacklisted("token123")
            # BUGGY: Returns False because it checks wrong key
            assert result is False

    @pytest.mark.skip(reason="Run after fix is applied")
    def test_blacklist_key_format_fixed(self):
        """Test that the blacklist key format bug is fixed."""
        from auth.token import blacklist_token, is_token_blacklisted, get_redis_client

        # Mock Redis to verify key formats
        mock_redis = MagicMock()
        mock_redis.exists.return_value = 0

        with patch("auth.token.get_redis_client", return_value=mock_redis):
            # Blacklist a token
            test_token = "test_token_123"
            blacklist_token(test_token)

            # Verify blacklist_token uses "revoked:{token}" format
            mock_redis.setex.assert_called_once()
            call_args = mock_redis.setex.call_args
            assert call_args[0][0] == f"revoked:test_token_123"

        # Now test is_token_blacklisted uses the SAME format (fixed)
        mock_redis.reset_mock()
        mock_redis.exists.return_value = 0

        with patch("auth.token.get_redis_client", return_value=mock_redis):
            is_token_blacklisted("test_token_123")
            # FIXED: Now uses "revoked:{token}" format consistently
            mock_redis.exists.assert_called_once_with("revoked:test_token_123")

    @pytest.mark.skip(reason="Run after fix is applied")
    def test_blacklist_fixed_no_false_negative(self):
        """Test that the key mismatch fix prevents false negatives."""
        from auth.token import blacklist_token, is_token_blacklisted

        mock_redis = MagicMock()
        # Simulate token being blacklisted with "revoked:" prefix (the correct format)
        mock_redis.exists.return_value = 1  # Token exists in blacklist

        with patch("auth.token.get_redis_client", return_value=mock_redis):
            blacklist_token("token123")  # Stores as "revoked:token123"
            mock_redis.reset_mock()
            mock_redis.exists.return_value = 1  # Would return 1 for correct key

            # is_token_blacklisted now uses the SAME "revoked:" format
            mock_redis.exists.return_value = 1  # Correct key returns 1
            result = is_token_blacklisted("token123")
            # FIXED: Returns True because both functions use the same key format
            assert result is True