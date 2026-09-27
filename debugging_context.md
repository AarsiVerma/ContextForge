# Context Package: Debug OAuth refresh 401
**Task ID:** demo-auth-001
**Compiled:** 2026-09-27T02:02:28.084676
**Estimated Tokens:** 1787

## TASK
**Task:** Debug OAuth refresh 401

**Task ID:** demo-auth-001
**Details:** Debug OAuth refresh 401


## PROVENANCE
- user:developer (observed by developer, confidence 100%)
- file:tests\test_auth.py (observed by file_ingestion, confidence 100%)
- file:auth\token.py (observed by file_ingestion, confidence 100%)
- file:auth\endpoints.py (observed by file_ingestion, confidence 100%)
- file:tests\conftest.py (observed by file_ingestion, confidence 100%)
- file:tests\test_bugs.py (observed by file_ingestion, confidence 100%)


## REJECTED HYPOTHESES
- JWT secret mismatch — *Rejected: FALSE* (debugger)
- Refresh token rotation race condition — *Rejected: INCONCLUSIVE* (debugger)


## RELEVANT FILES
- `auth\token.py` — ... [truncated]     payload = decode_token(token)
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
- `auth\endpoints.py` — ... [truncated]             status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token required",
        )

    # Check blacklist - BUG: uses wrong key format
    if is_token_blacklisted(refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    try:
        payload = validate_refresh_token(refresh_token)
        username = payload.get("sub")
        user_id = payload.get("user_id")

        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        # Check if user still exists and is active
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Blacklist old refresh token (rotation)
        blacklist_token(refresh_token)

        # Issue new token pair
        token_data = {"sub": username, "user_id": user_id, "roles": user.get_role_names()}
        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Refresh token error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )


@router.post("/logout")
async def logout(
    request: Request,
    token: str = Depends(oauth2_scheme),
):
    """Logout user by blacklisting tokens."""
    body = await request.json()
    refresh_token = body.get("refresh_token")
 ... [truncated]
- `tests\conftest.py` — ... [truncated] 

@pytest.fixture
def admin_user(db_session):
    """Create an admin user with role."""
    from auth.models import User, Role
    admin_role = Role(name="admin", description="Administrator")
    db_session.add(admin_role)
    db_session.commit()
    db_session.refresh(admin_role)

    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password="hashed_admin123",
        is_active=True
    )
    user.roles.append(admin_role)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user."""
    response = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "password123"}
    ) ... [truncated]
- `tests\test_auth.py` — ... [truncated]             # Verify blacklist_token uses "revoked:{token}" format
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

    def test_blacklist_buggy_false_negative(self): ... [truncated]
- `tests\test_bugs.py` — ... [truncated]         # This test documents the expected behavior
        assert page1_max < page2_min, "Pagination order should be consistent (by ID)"


class TestBugCACHE004:
    """Tests for BUG CACHE-004: Stale user permissions in JWT."""

    def test_permission_change_not_reflected_immediately(self, client, db_session):
        """Test that permission changes aren't reflected until token refresh."""
        from auth.token import create_access_token, validate_access_token
        from auth.models import Role

        # Create user and admin role
        user = User(username="permuser", email="perm@test.com", hashed_password="hashed_pass")
        admin_role = Role(name="admin", description="Administrator")
        db_session.add_all([user, admin_role])
        db_session.commit() ... [truncated]

