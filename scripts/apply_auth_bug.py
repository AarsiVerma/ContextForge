#!/usr/bin/env python3
"""Apply AUTH-001 bug: Redis key mismatch."""

with open('demo-app/auth/token.py', 'r') as f:
    content = f.read()

# Apply bug: change revoked: to blacklist: in is_token_blacklisted
content = content.replace('client.exists(f"revoked:{token}")', 'client.exists(f"blacklist:{token}")')

# Update comment
content = content.replace(
    '# FIXED: Uses "revoked:{token}" to match blacklist_token storage',
    '# BUG: Checks "blacklist:{token}" but blacklist_token stores "revoked:{token}"'
)

with open('demo-app/auth/token.py', 'w') as f:
    f.write(content)

print("AUTH-001 bug applied")