# OAuth Refresh Debugging Project

Configuration for the OAuth authentication service.

## Environment Variables

```env
JWT_SECRET=dev-secret-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
DATABASE_URL=postgresql://user:pass@localhost/dbname
REDIS_URL=redis://localhost:6379/0
```

## Token Configuration

- Access tokens expire in 30 minutes
- Refresh tokens expire in 7 days
- Token rotation enabled (old refresh token blacklisted on refresh)
- Algorithm: HS256

## Known Issues

1. Refresh endpoint returns 401 for valid refresh tokens
2. Token blacklist not implemented (Redis integration pending)
3. Race condition possible in concurrent refresh requests

## Debugging Notes

- Check token payload structure in `auth/token.py`
- Verify refresh token validation logic
- Monitor Redis connection for blacklist
- Review concurrent request handling