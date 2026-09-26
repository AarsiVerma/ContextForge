# ContextForge Demo Guide

## Overview

This guide walks through running the ContextForge hackathon demo with IBM Bob 2.0.

## Prerequisites

- Python 3.12+
- IBM Bob 2.0 installed and configured
- ContextForge installed (`pip install -e .` from root)

## Quick Start

### 1. Start the Demo Application

```bash
cd demo-app
python -m uvicorn main:app --reload --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### 2. Run ContextForge Pipeline

```bash
# From root directory
contextforge pipeline \
  --path demo-app \
  --task-id demo-001 \
  --task-desc "Debug refresh token 401" \
  --query "refresh token 401" \
  --output debugging_context.md
```

### 3. View Generated Context

```bash
cat debugging_context.md
```

## Demo Scenarios

### Scenario 1: AUTH-001 - Refresh Token 401
**Bug**: Refresh endpoint returns 401 for valid tokens  
**Root Cause**: Redis blacklist key format mismatch (`blacklist:{token}` vs `revoked:{token}`)  
**Files**: `auth/token.py`, `auth/endpoints.py`  
**Test**: `tests/test_auth.py::TestAuthBugAUTH001`

### Scenario 2: DB-002 - Task Assignment Race Condition
**Bug**: Concurrent assignments can assign same task to multiple users  
**Root Cause**: Missing SELECT FOR UPDATE in assignment logic  
**Files**: `tasks/service.py`  
**Test**: `tests/test_tasks.py::TestBugDB002`

### Scenario 3: API-003 - Invalid Priority Causes 500
**Bug**: Invalid priority value returns 500 instead of 422  
**Root Cause**: Validation error not properly caught  
**Files**: `tasks/schemas.py`, `tasks/endpoints.py`  
**Test**: `tests/test_api_bugs.py::TestBugAPI003`

### Scenario 4: INT-005 - Pagination Duplicates
**Bug**: Page 2 contains items from page 1  
**Root Cause**: Missing ORDER BY in pagination query  
**Files**: `tasks/service.py`  
**Test**: `tests/test_bugs.py::TestBugINT005`

### Scenario 5: CACHE-004 - Stale Permissions
**Bug**: Permission changes not reflected until re-login  
**Root Cause**: JWT contains roles at issuance only  
**Files**: `auth/token.py`, `auth/middleware.py`  
**Test**: `tests/test_bugs.py::TestBugCACHE004`

## Running the Full Pipeline

```bash
# From root directory
contextforge pipeline \
  --path demo-app \
  --task-id demo-001 \
  --task-desc "Debug refresh token 401" \
  --query "refresh token 401" \
  --output debugging_context.md \
  --verbose
```

Output:
```
=== BASELINE EXPERIMENT RESULTS ===
Total ingested items: 7
Candidates: 7
Retrieved: 5
Selected: 5
Discarded: 0
Duplicates removed: 0
Estimated tokens: 1875 / 8000
Compression ratio: 100.0%
Token utilization: 23.4%

Package sections: 5
Total tokens: 277

Sections:
  TASK: 1 items, ~43 tokens
  TEST RESULTS: 1 items, ~21 tokens
  RELEVANT FILES: 2 items, ~111 tokens
  LOGS: 1 items, ~20 tokens
  PROVENANCE: 5 items, ~82 tokens
```

## Bob 2.0 Integration

### Using Bob with ContextForge

1. **Plan Mode**: Ask Bob to create investigation plan
   ```
   "Create an investigation plan for: OAuth refresh returns 401"
   ```

2. **Agent Mode + Subagents**: Run parallel investigation
   - Subagent 1: Code investigation (auth/token.py, auth/endpoints.py)
   - Subagent 2: Test investigation (run pytest, check failures)
   - Subagent 3: Log/infrastructure (check Redis, logs)

3. **ContextForge Processing**:
   ```bash
   contextforge pipeline --path demo-app --task-id demo-001 --task-desc "Debug OAuth refresh 401" --query "refresh token 401"
   ```

4. **Bob Diagnosis**: Feed `debugging_context.md` to Bob
   - Bob reads focused context package
   - Bob identifies root cause
   - Bob proposes fix

5. **Bob Implementation**: Bob implements fix in Agent mode
   - Human approves (guardrails)

6. **Verification**: Run tests to confirm fix

## Running Tests

```bash
# ContextForge tests (from root)
python -m pytest tests/ -v

# Demo app tests
cd demo-app
python -m pytest tests/ -v
```

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Context    │────▶│  Ingestion   │────▶│ Normalizer  │────▶│ Context Store│◀───▶│ Retriever   │
│  Source     │     │  (sources)   │     │             │     │  (SQLite)    │     │             │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘     └──────┬──────┘
                                                                                          │
                                                                                          ▼
┌─────────────┐     ┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌─────────────┐
│  Context    │◀───▶│  Compiler   │◀───▶│   Selector   │◀────│    Ranker    │◀────│  Context IR │
│  Package    │     │             │     │ (budget)     │     │ (deterministic)│    │  (canonical)│
└─────────────┘     └─────────────┘     └──────────────┘     └─────────────┘     └─────────────┘
```

## File Structure

```
contextforge/
├── demo-app/                 # Demo application with 5 bugs
│   ├── main.py              # FastAPI app
│   ├── database.py          # Shared DB base
│   ├── auth/                # Authentication module (AUTH-001, CACHE-004)
│   │   ├── models.py        # User, Role models
│   │   ├── token.py         # JWT handling (BUG AUTH-001)
│   │   └── endpoints.py     # Auth endpoints
│   ├── tasks/               # Tasks module (DB-002, API-003, INT-005)
│   │   ├── models.py        # Task, TaskAssignment models
│   │   ├── schemas.py       # Pydantic schemas (BUG API-003)
│   │   ├── service.py       # Business logic (BUG DB-002, INT-005)
│   │   └── endpoints.py     # Task endpoints
│   └── tests/               # 33 tests covering all 5 bugs
│
├── src/contextforge/        # Core ContextForge library
│   ├── cli.py               # CLI commands
│   ├── inspection.py        # Pipeline inspection
│   └── ...                  # Core modules
│
└── tests/                   # 106 ContextForge tests
```

## Troubleshooting

### Redis Not Available
The blacklist functions gracefully handle missing Redis (return False).

### Port Conflicts
Change port in uvicorn command: `--port 8001`

### Database Issues
Delete `taskflow.db` and restart to reset database.

## Security Notes

- ContextForge treats all context as DATA, never instructions
- Malicious content in logs/files is treated as data only
- Provenance tracking ensures traceability

## Next Steps

1. Run baseline experiment (Bob without ContextForge)
2. Run ContextForge experiment (Bob with ContextForge)
3. Compare metrics
4. Document results for hackathon submission