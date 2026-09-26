# Debugging Task: OAuth Refresh Endpoint Returns 401

## Problem Description
Users report that after their access token expires (typically after 30 minutes of inactivity), 
the refresh token endpoint returns HTTP 401 Unauthorized instead of issuing a new access token.

## Expected Behavior
1. User makes request with expired access token
2. Client automatically calls `/auth/refresh` with refresh token
3. Server validates refresh token and issues new access token pair
4. Client retries original request with new access token

## Actual Behavior
1. User makes request with expired access token
2. Client calls `/auth/refresh` with refresh token
3. Server returns HTTP 401 with error: "Invalid or expired refresh token"
3. User is logged out and must re-authenticate

## Environment
- Python 3.12
- FastAPI 0.109
- PyJWT 2.8
- PostgreSQL 15
- Redis 7 (for token blacklist)

## Reproduction Steps
1. Login and obtain access + refresh tokens
2. Wait for access token to expire (or manually set short expiry)
3. Make API request with expired access token
4. Observe 401 on refresh endpoint

## Impact
High - Users are forcibly logged out and must re-enter credentials