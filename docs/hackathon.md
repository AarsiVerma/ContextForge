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

**ContextForge makes IBM Bob 2.0 better at multi-step debugging by continuously maintaining and selecting the evidence and debugging state Bob actually needs, instead of forcing the agent to repeatedly rediscover it.**

> **Don't give the AI more context. Give it the right context.**

## How ContextForge Uses Bob

### Bob Capabilities Leveraged

1. **Plan Mode** - Create structured investigation plans from bug reports
2. **Agent Mode** - Execute investigation and implement fixes
3. **Subagents** - Parallel investigation streams with isolated contexts
4. **Guardrails** - Human approval before code changes
5. **Bob Shell (CLI)** - Automated workflow execution
6. **MCP** - Optional integration for context queries

### Workflow

```text
Bug Report
    ↓
Bob Plan Mode: Create investigation plan
    ↓
Bob Agent Mode + Subagents: Parallel investigation
    ↓
    ├─ Code investigation
    ├─ Test investigation  
    └─ Log/infrastructure investigation
    ↓
ContextForge Pipeline:
    Collect → Normalize → Deduplicate → Retrieve → Rank → Select → Compile
    ↓
Focused Debugging Context Package (markdown)
    ↓
Bob Agent Mode: Diagnose root cause from focused context
    ↓
Bob Agent Mode: Implement fix
    ↓
Run verification tests
    ↓
ContextForge: Record result, update debugging state
    ↓
Complete
```

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

### 5 Reproducible Bug Scenarios

#### Bug 1: Authentication - Refresh Token Returns 401
- **ID**: AUTH-001
- **Title**: Refresh endpoint returns 401 for valid refresh tokens
- **Symptom**: Users get logged out after access token expires; refresh fails
- **Reproduction**: Login → wait for access token expiry → call /auth/refresh → 401
- **Expected**: New access token pair issued
- **Actual**: 401 "Invalid or expired refresh token"
- **Relevant Files**: `auth/token.py`, `auth/endpoints.py`
- **Tests**: `tests/test_auth.py::test_refresh_endpoint_success`
- **Noise**: Database models, unrelated endpoints, documentation
- **Root Cause**: Refresh token validation checks blacklist before validating token signature; blacklist check uses wrong Redis key format
- **Expected Fix**: Fix Redis key format in `is_token_blacklisted()`
- **Verification**: `test_refresh_endpoint_success` passes

#### Bug 2: Database - Task Assignment Race Condition
- **ID**: DB-002
- **Title**: Concurrent task assignments can assign same task to multiple users
- **Symptom**: Two users claim same task simultaneously; both succeed
- **Reproduction**: Two simultaneous POST /tasks/{id}/assign requests
- **Expected**: Second request fails with 409 Conflict
- **Actual**: Both succeed, task assigned to last requester
- **Relevant Files**: `tasks/endpoints.py`, `tasks/service.py`
- **Tests**: `tests/test_tasks.py::test_concurrent_assignment`
- **Noise**: User model, auth middleware, unrelated task operations
- **Root Cause**: Missing SELECT FOR UPDATE / row-level lock in assignment logic
- **Expected Fix**: Add database lock or optimistic locking
- **Verification**: Concurrent assignment test passes

#### Bug 3: API Edge Case - Invalid Priority Value
- **ID**: API-003
- **Title**: Creating task with invalid priority causes 500 instead of 422
- **Symptom**: POST /tasks with priority="urgent" (not in enum) returns 500
- **Reproduction**: POST /tasks with invalid priority string
- **Expected**: 422 Unprocessable Entity with validation error
- **Actual**: 500 Internal Server Error (KeyError in priority handling)
- **Relevant Files**: `tasks/schemas.py`, `tasks/endpoints.py`
- **Tests**: `tests/test_tasks.py::test_invalid_priority`
- **Noise**: Valid priority handling, other validation logic
- **Root Cause**: Priority enum validation happens after model creation; KeyError not caught
- **Expected Fix**: Add Pydantic validator for priority field
- **Verification**: Invalid priority returns 422

#### Bug 4: State/Cache - Stale User Permissions
- **ID**: CACHE-004
- **Title**: User permission changes not reflected until re-login
- **Symptom**: Admin grants user new role; user still gets 403 until token refresh
- **Reproduction**: Grant role → immediate API call with existing token → 403
- **Expected**: Permission check uses current roles
- **Actual**: Cached roles in JWT used for authorization
- **Relevant Files**: `auth/middleware.py`, `auth/endpoints.py`
- **Tests**: `tests/test_auth.py::test_permission_change_immediate`
- **Noise**: Token validation, role hierarchy, other middleware
- **Root Cause**: JWT contains roles at issuance; no mechanism to invalidate on role change
- **Expected Fix**: Add role version to JWT or check DB on each request
- **Verification**: Permission change test passes

#### Bug 5: Interaction/Regression - Task Filter + Pagination
- **ID**: INT-005
- **Title**: Filtering tasks by status with pagination returns duplicate results
- **Symptom**: GET /tasks?status=open&page=2 returns some tasks from page 1
- **Reproduction**: Create 25 open tasks → request page 2 → observe duplicates
- **Expected**: Page 2 contains tasks 11-20
- **Actual**: Page 2 contains some tasks from 1-10
- **Relevant Files**: `tasks/endpoints.py`, `tasks/service.py`
- **Tests**: `tests/test_tasks.py::test_pagination_no_duplicates`
- **Noise**: Other filters, sorting, other endpoints
- **Root Cause**: Pagination offset calculated before filter applied
- **Expected Fix**: Apply filter before pagination offset
- **Verification**: Pagination test passes

## Demo Flow

### Setup (30 seconds)
```bash
# Start demo application
cd demo-app
python -m uvicorn main:app --reload &
# Start ContextForge CLI
contextforge pipeline --path . --task-id demo-001 --task-desc "Debug refresh token 401" --query "refresh token 401"
```

### Phase 1: Bob Plan Mode (1 minute)
- Human: "Here's the bug: refresh token returns 401"
- Bob Plan Mode: Creates investigation plan with 3 streams

### Phase 2: Parallel Investigation (2 minutes)
- Subagent 1: Code investigation (auth/token.py, auth/endpoints.py)
- Subagent 2: Test investigation (run tests, check failures)
- Subagent 3: Log/infrastructure investigation (check Redis, logs)
- Each returns concise summary

### Phase 3: ContextForge Processing (30 seconds)
```bash
contextforge pipeline --path . --task-id demo-001 --task-desc "Debug refresh token 401" --query "refresh token 401" --output debugging_context.md
```
- Generates focused debugging context package

### Phase 4: Bob Diagnosis (1 minute)
- Bob reads debugging_context.md
- Bob identifies root cause: Redis key format in blacklist check
- Bob proposes fix

### Phase 5: Bob Implementation (1 minute)
- Bob Agent Mode implements fix in auth/token.py
- Human approves change (guardrails)

### Phase 6: Verification (30 seconds)
- Run test suite
- All tests pass
- ContextForge records result

### Phase 7: ContextForge State Update (15 seconds)
- Records root cause, fix, verification
- Preserves rejected hypotheses
- Ready for next debugging session

## Measurable Impact

### Baseline (Bob without ContextForge)
- Time to resolution: ~8-10 minutes
- Files inspected: 15-20
- Tool operations: 30-40
- Repeated hypotheses: 2-3
- Failed repair attempts: 1-2

### With ContextForge
- Time to resolution: ~4-5 minutes
- Files inspected: 5-8 (focused)
- Tool operations: 15-20
- Repeated hypotheses: 0 (tracked)
- Failed repair attempts: 0

### Context Metrics
- Raw context items: ~50
- Retrieved: ~20
- Duplicates removed: ~5
- Selected: ~12
- Discarded: ~38
- Estimated tokens: ~2,100 / 8,000 budget
- Rejected hypotheses preserved: 3

## Limitations

1. **No direct Bob API** - Using file-based handoff
2. **Subagents are Bob-internal** - Cannot programmatically control
3. **No programmatic session control** - Human-in-the-loop required
4. **Local JEV experimental** - Not required for MVP
5. **Single-user, local only** - No multi-user/auth

## Future Work

1. Direct MCP integration with Bob
2. Local JEV/ranker for improved selection
3. Evaluation harness with ground-truth labels
4. Multi-bug debugging session support
5. IDE integration (VS Code extension)
6. Team/shared debugging state