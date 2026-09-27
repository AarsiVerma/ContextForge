nextnow ag#!/usr/bin/env bash
set -euo pipefail

# reset_bug.sh <BUG_ID>
# Applies buggy version of a specific bug for demo/evaluation

BUG_ID="${1:-}"
if [[ -z "$BUG_ID" ]]; then
    echo "Usage: $0 <BUG_ID>"
    echo "Available bugs: AUTH-001, INT-005, API-003, DB-002, CACHE-004"
    exit 1
fi

CONTEXTFORGE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEMO_APP="$CONTEXTFORGE_ROOT/demo-app"

case "$BUG_ID" in
    AUTH-001)
        echo "Applying AUTH-001 bug: Redis key mismatch (blacklist: vs revoked:)"
        # Bug: is_token_blacklisted checks "blacklist:{token}" but storage uses "revoked:{token}"
        sed -i 's/client.exists(f"revoked:{token}")/client.exists(f"blacklist:{token}")/' "$DEMO_APP/auth/token.py"
        sed -i 's/# FIXED: Uses "revoked:{token}" to match blacklist_token storage/# BUG: Checks "blacklist:{token}" but blacklist_token stores "revoked:{token}"/' "$DEMO_APP/auth/token.py"
        sed -i 's/# BUG: Uses "revoked:{token}" but blacklist_token stores "revoked:{token}"/# BUG: Checks "blacklist:{token}" but blacklist_token stores "revoked:{token}"/' "$DEMO_APP/auth/token.py"
        echo "AUTH-001 bug applied. Run test to verify failure."
        ;;
    INT-005)
        echo "Applying INT-005 bug: Remove ORDER BY from pagination"
        # Bug: Remove order_by(Task.id) from list_tasks
        sed -i '/query = query.order_by(Task.id)/d' "$DEMO_APP/tasks/service.py"
        echo "INT-005 bug applied. Run test to verify failure."
        ;;
    API-003)
        echo "Applying API-003 bug: Invalid priority causes 500"
        # This requires more complex changes - placeholder
        echo "API-003: Not yet implemented in reset script"
        ;;
    DB-002)
        echo "Applying DB-002 bug: Race condition (already present in code)"
        # The race condition bug is already in the code (no SELECT FOR UPDATE)
        echo "DB-002: Bug already present in code"
        ;;
    CACHE-004)
        echo "Applying CACHE-004 bug: Stale permissions in JWT (already present)"
        # The JWT design bug is already in the code
        echo "CACHE-004: Bug already present in code"
        ;;
    *)
        echo "Unknown bug: $BUG_ID"
        exit 1
        ;;
esac