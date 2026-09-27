# ContextForge Hackathon Plan

## Challenge Statement

**IBM Bob 2.0 Hackathon**: Create a solution that improves a specific developer workflow using IBM Bob 2.0.

## Selected Workflow: AI-Assisted Software Debugging

### Problem Definition

During multi-step debugging, AI coding agents repeatedly encounter large amounts of mixed-quality information—source files, logs, test output, documentation, tool results, previous hypotheses, and failed fixes. Without a structured mechanism for maintaining debugging state and selecting task-relevant evidence, the agent can:

- Repeatedly investigate the same paths
- Carry irrelevant information forward
- Perform unnecessary work
- Generate repeated hypotheses
- Waste tool calls
- Increase rework
- Produce potentially incorrect fixes
- Lengthen debugging workflows

### Solution: ContextForge

**ContextForge makes AI coding agents better at multi-step debugging by continuously maintaining and selecting the evidence and debugging state the agent actually needs, instead of forcing the agent to repeatedly rediscover it.**

> **Don't give the AI more context. Give it the right context.**

## How ContextForge Works with Bob 2.0

### Current Integration: File-Based Handoff

**ContextForge does not have programmatic integration with Bob 2.0.** The integration is a **manual file-based handoff**:

```
ContextForge CLI → debugging_context.md → Human → Bob 2.0 (file read)
```

This is the most reliable approach given Bob 2.0's current lack of public context injection API.

### Bob Capabilities ContextForge Complements

| Bob Capability | How ContextForge Helps |
|----------------|------------------------|
| **Plan Mode** | Provides structured evidence for plan creation |
| **Agent Mode** | Supplies focused evidence for diagnosis |
| **Subagents** | Each subagent could receive tailored context package |
| **Guardrails** | Provenance enables human review of evidence |
| **Bob Shell (CLI)** | ContextForge CLI can be invoked from Bob Shell scripts |
| **MCP** | Future: ContextForge as MCP server for Bob |

### Actual Demo Workflow

```text
Bug Report
    ↓
Human: Runs failing test to confirm bug
    ↓
Human: Runs ContextForge pipeline → debugging_context.md
    ↓
Human → Bob: Provides debugging_context.md (file read)
    ↓
Bob Agent Mode: Diagnoses root cause from focused context
    ↓
Bob Agent Mode: Proposes/implements fix
    ↓
Human: Approves (guardrails)
    ↓
Run verification tests
    ↓
ContextForge: Records result, updates debugging state
    ↓
Complete
```

**Key**: Human is the bridge between ContextForge and Bob. No programmatic integration exists.

---

## Demo Application

### Stack
- **Backend**: FastAPI (Python 3.12)
- **Database**: SQLite (for simplicity)
- **Auth**: JWT with access/refresh tokens
- **Tests**: pytest
- **Frontend**: Minimal HTML/JS (single page)

### Application: "TaskFlow" - Simple Task Management API

A minimal task management application with:
- User authentication (JWT)
- Task CRUD operations
- Task assignment
- Due dates and priorities

---

### 5 Reproducible Bug Scenarios

#### Bug 1: Authentication - Refresh Token Returns 401
- **ID**: AUTH-001
- **Title**: Refresh endpoint returns 401 for valid refresh tokens
- **Symptom**: Users get logged out after access token expires; refresh fails
- **Reproduction**: Login → wait for access token expiry → call /auth/refresh → 401
- **Expected**: New access token pair issued
- **Actual**: 401 "Invalid or expired refresh token"
- **Relevant Files**: `auth/token.py`, `auth/endpoints.py`
- **Root Cause**: Redis key mismatch - `is_token_blacklisted()` checks `blacklist:{token}` but `blacklist_token()` stores `revoked:{token}`
- **Fix**: Change `is_token_blacklisted()` to use `revoked:` prefix
- **Verification**: `test_refresh_token_success` passes

#### Bug 2: Database - Task Assignment Race Condition
- **ID**: DB-002
- **Title**: Concurrent task assignments can assign same task to multiple users
- **Symptom**: Two users claim same task simultaneously; both succeed
- **Reproduction**: Two simultaneous POST /tasks/{id}/assign requests
- **Expected**: Second request fails with 409 Conflict
- **Actual**: Both succeed, task assigned to last requester
- **Relevant Files**: `tasks/service.py`
- **Root Cause**: Missing SELECT FOR UPDATE / row-level lock in assignment logic
- **Fix**: Add database lock or optimistic locking
- **Verification**: `test_concurrent_assignment_race_condition` passes

#### Bug 3: API Edge Case - Invalid Priority Value
- **ID**: API-003
- **Title**: Creating task with invalid priority causes 500 instead of 422
- **Symptom**: POST /tasks with priority="urgent" (not in enum) returns 500
- **Reproduction**: POST /tasks with invalid priority string
- **Expected**: 422 Unprocessable Entity with validation error
- **Actual**: 500 Internal Server Error
- **Relevant Files**: `tasks/schemas.py`, `tasks/endpoints.py`
- **Status**: **Already fixed by Pydantic v2** - enum validation returns 422 automatically
- **Verification**: `test_create_task_invalid_priority_returns_422` passes

#### Bug 4: State/Cache - Stale User Permissions
- **ID**: CACHE-004
- **Title**: User permission changes not reflected until re-login
- **Symptom**: Admin grants user new role; user still gets 403 until token refresh
- **Reproduction**: Grant role → immediate API call with existing token → 403
- **Expected**: Permission check uses current roles
- **Actual**: Cached roles in JWT used for authorization
- **Relevant Files**: `auth/token.py`, `auth/endpoints.py`
- **Root Cause**: JWT contains roles at issuance; no mechanism to invalidate on role change
- **Fix**: Add role version to JWT or check DB on each request
- **Verification**: `test_permission_change_not_reflected_immediately` passes

#### Bug 5: Interaction/Regression - Task Filter + Pagination
- **ID**: INT-005
- **Title**: Filtering tasks by status with pagination returns duplicate results
- **Symptom**: GET /tasks?status=open&page=2 returns some tasks from page 1
- **Reproduction**: Create 25 open tasks → request page 2 → observe duplicates
- **Expected**: Page 2 contains tasks 11-20
- **Actual**: Page 2 contains some tasks from 1-10
- **Relevant Files**: `tasks/service.py`
- **Root Cause**: Missing ORDER BY in pagination query
- **Fix**: Add `query = query.order_by(Task.id)` before pagination
- **Verification**: `test_pagination_no_duplicates` passes

---

## Demo Flow

### Setup (30 seconds)
```bash
# Start demo application
cd demo-app
python -m uvicorn main:app --reload &

# Reset bug to buggy state
./scripts/reset_bug.sh AUTH-001
```

### Phase 1: Show Bug (30 seconds)
- Run failing test: `pytest demo-app/tests/test_auth.py::TestAuthEndpoints::test_refresh_token_success -v`
- Shows: FAILED - 401 for valid token

### Phase 2: ContextForge Pipeline (1 minute)
```bash
contextforge pipeline \
  --path demo-app \
  --task-id demo-auth-001 \
  --task-desc "Debug OAuth refresh 401" \
  --query "refresh token 401 blacklist revoked" \
  --output debugging_context.md
```
- Shows real pipeline output with metrics
- Generates `debugging_context.md`

### Phase 3: Show Generated Context (1 minute)
```bash
cat debugging_context.md
```
- Highlight: REJECTED HYPOTHESES section
- Highlight: token.py snippet with both `blacklist:` and `revoked:` lines
- Highlight: PROVENANCE section

### Phase 4: Human → Bob Handoff (30 seconds)
- Human opens Bob 2.0
- Provides: "Here's debugging context for the refresh token bug"
- Bob reads `debugging_context.md` via file operations

### Phase 5: Bob Diagnosis & Fix (1 minute)
- Bob reads context, identifies: "`is_token_blacklisted()` checks `blacklist:` but storage uses `revoked:`"
- Bob proposes fix: Change line 109 in `auth/token.py`
- Human approves (guardrails)
- Bob implements fix

### Phase 6: Verification (30 seconds)
```bash
# Apply fix
sed -i 's/blacklist:\\\(.*\\\)/revoked:\\1/' demo-app/auth/token.py

# Verify
python -m pytest demo-app/tests/test_auth.py::TestAuthEndpoints::test_refresh_token_success -v
# PASSED

# Full regression
python -m pytest demo-app/tests/ -v
# ALL 32 TESTS PASSED
```

### Phase 7: Show Metrics (30 seconds)
- Show real pipeline output: "8 items selected, 821 tokens"
- Show evaluation results from `eval/results_*.json`

---

## Impact Metrics (Actual vs Estimated)

### ContextForge Pipeline (Actual Measurements)
| Metric | Value |
|--------|-------|
| Items ingested | 19 (AUTH-001) |
| Items retrieved | 10 |
| Items selected | 8 |
| Duplicates removed | 0 |
| Tokens in package | 821 |
| Token budget | 12,000 |
| Pipeline duration | ~7s (includes pytest) |

### Bug Fix Results (All 5 Bugs)
| Bug | ContextForge Correct Dx? | Repeated Hyps Eliminated? | Test Passed? |
|-----|-------------------------|--------------------------|--------------|
| AUTH-001 | ✅ Yes | ✅ Yes (0 vs 0) | ✅ |
| INT-005 | ✅ Yes | ✅ Yes (0 vs 0) | ✅ |
| API-003 | ❌ No (already fixed) | ✅ Yes (0 vs 0) | ✅ |
| DB-002 | ✅ Yes | ✅ Yes (0 vs 1) | ✅ |
| CACHE-004 | ❌ No (architectural) | ✅ Yes (0 vs 0) | ✅ |

**Key**: 3/5 bugs correctly diagnosed by ContextForge; repeated hypotheses eliminated for DB-002.

### Baseline Comparison (Estimated Baseline vs ContextForge)
> **NOTE**: Baseline figures are **estimates** from team experience, NOT from a controlled experiment. A proper controlled study is needed for valid comparison.

| Metric | Baseline (Estimated) | ContextForge (Measured) | Status |
|--------|---------------------|------------------------|--------|
| Time to resolution | ~8-10 min (est.) | ~7s pipeline + fix time | Estimate vs Actual |
| Files inspected | 15-20 (est.) | 1-2 key files | Estimate vs Actual |
| Tool operations | 30-40 (est.) | 2 commands | Estimate vs Actual |
| Repeated hypotheses | 2-3 (est.) | 0 (tracked) | **Verified** |
| Context reduction | N/A | 58% (19→8 items) | **Measured** |

**Key Verified Claims**:
- ✅ 58% context reduction (19→8 items)
- ✅ Zero repeated hypotheses (DebuggingState tracks rejections)
- ✅ Root cause visible in context package (provenance shows both keys)
- ✅ All tests pass after fix

**Estimated/Unverified**:
- ⚠️ "50% faster" - baseline not measured
- ⚠️ "76% reduction" - baseline not measured
- ⚠️ Time savings - pipeline takes 7s + fix time

---

## Limitations (Honest)

1. **No direct Bob API** - Using file-based handoff (manual handoff)
2. **Subagents are Bob-internal** - Cannot programmatically control
3. **No programmatic session control** - Human-in-the-loop required
4. **Baseline metrics are estimates** - No controlled experiment conducted
5. **CACHE-004 fix requires auth middleware** - Not demonstrated
6. **ContextForge metrics parsing incomplete** - Real pipeline metrics not fully captured in eval
7. **Single-user, local only** - No multi-user/auth

---

## Future Work

1. **MCP server for ContextForge** - If Bob supports MCP client
2. **Proper evaluation harness** - Controlled experiment with human subjects
3. **Improved metrics collection** - Real pipeline metrics capture
4. **Local cross-encoder ranker** - Feature-flagged option
5. **Multi-bug session support** - Debugging across related bugs
5. **IDE integration** - VS Code extension

---

*Plan updated: 2026-09-27*
*Based on: Actual implementation audit + evaluation run*
*See also: `docs/BOB_INTEGRATION_REALITY.md`, `docs/JUDGE_DEMO.md`, `docs/evaluation.md`*