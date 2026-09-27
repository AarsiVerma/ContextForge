# Judge Demo Script - ContextForge + IBM Bob 2.0

## Demo Overview

**Duration**: 5 minutes  
**Format**: Live terminal + Bob 2.0 interaction  
**Core Message**: "ContextForge gives Bob the right context, not more context"

---

## Demo Script (5 Minutes)

### 0:00-0:30 — Setup & Bug Reproduction
**Speaker**: "We'll demonstrate ContextForge on a real bug in a production-like API."

**Commands**:
```bash
# 1. Show the bug exists
cd demo-app
python -m pytest tests/test_auth.py::TestAuthEndpoints::test_refresh_token_success -v
# Shows: FAILED - 401 Unauthorized for valid refresh token
```

**Say**: "This is AUTH-001: valid refresh tokens get rejected with 401. The bug is a Redis key mismatch."

---

### 0:30-1:30 — ContextForge Pipeline
**Speaker**: "Now we run ContextForge to generate focused debugging context."

**Commands**:
```bash
# 2. Run ContextForge (generates real metrics)
contextforge pipeline \
  --path demo-app \
  --task-id demo-auth-001 \
  --task-desc "Debug OAuth refresh 401" \
  --query "refresh token 401 blacklist revoked" \
  --output debugging_context.md
```

**Expected Output**:
```
Pipeline complete: 8 items selected, 821 tokens

=== CONTEXTFORGE PIPELINE INSPECTION ===
[1] INGESTION:     19 items from 4 sources
[2] RETRIEVAL:     10 candidates → 8 retrieved
[3] RANKING:       8 items ranked by 6 signals
[4] SELECTION:     8 selected (0 duplicates, 8000 token budget)
[5] COMPILATION:   6 sections, 821 tokens
```

**Say**: "ContextForge ingested 19 items, ranked them by relevance/freshness/importance, selected 8 under token budget. Notice the REJECTED HYPOTHESES section — ContextForge remembers what was already ruled out."

---

### 1:30-2:30 — Show Generated Context
**Speaker**: "Let's look at what Bob actually receives."

**Commands**:
```bash
cat debugging_context.md
```

**Key Sections to Highlight**:
1. **TASK** - Clear problem statement
2. **REJECTED HYPOTHESES** - "JWT secret mismatch (FALSE)", "Race condition (INCONCLUSIVE)"
3. **RELEVANT FILES** - `auth/token.py` with smart snippets showing BOTH `blacklist:` and `revoked:` lines
4. **PROVENANCE** - Full traceability: who observed what, when, confidence

**Say**: "Notice the token.py snippet shows both the buggy `blacklist:` check AND the correct `revoked:` storage. Bob doesn't need to search - the root cause is right there."

---

### 2:30-3:30 — Human → Bob Handoff
**Speaker**: "Now we give this context to Bob. This is a file-based handoff - Bob reads the file."

**Action**: 
- Open Bob 2.0
- Provide: "Here's the debugging context for the refresh token bug"
- Bob reads `debugging_context.md` (via file operations)

**Say**: "This is the current integration: file-based handoff. Bob reads the context package we generated."

---

### 3:30-4:00 — Bob Diagnosis & Fix
**Speaker**: "Bob now has focused context. Let's see what Bob does."

**Expected Bob Actions**:
1. Bob reads `debugging_context.md`
2. Bob identifies: "The bug is in `auth/token.py` - `is_token_blacklisted()` checks `blacklist:{token}` but `blacklist_token()` stores `revoked:{token}`"
3. Bob proposes fix: Change line 109 from `blacklist:` to `revoked:`
4. Human approves (guardrails)
5. Bob implements fix

**Say**: "Bob immediately sees the root cause because ContextForge put the relevant lines in front of him. No searching 20 files. No repeated hypotheses."

---

### 4:00-4:30 — Verification
**Speaker**: "Let's verify the fix works."

**Commands**:
```bash
# Apply fix (Bob would do this)
sed -i 's/blacklist:\\\(.*\\\)/revoked:\\1/' demo-app/auth/token.py

# Verify
python -m pytest demo-app/tests/test_auth.py::TestAuthEndpoints::test_refresh_token_success -v
# PASSED

# Full regression
python -m pytest demo-app/tests/ -v
# ALL 32 TESTS PASSED
```

---

### 4:30-5:00 — Metrics & Summary
**Speaker**: "Here are the real results from our evaluation across 5 bugs."

**Show Results Table**:
| Bug | Baseline Time | CF Time | Baseline Files | CF Files | Baseline Hyps | CF Hyps | Result |
|-----|--------------|---------|----------------|----------|---------------|---------|--------|
| AUTH-001 | 1.9s | 7.1s | 2 | 2 | 0→1 | 0→0 | ✅ Fixed |
| INT-005 | 1.9s | 7.4s | 1 | 1 | 0→1 | 0→0 | ✅ Fixed |
| API-003 | 1.9s | 7.4s | 2 | 2 | 0→1 | 0→0 | ✅ Fixed |
| DB-002 | 4.5s | 6.4s | 1 | 1 | 3→1 | 1→0 | ✅ Fixed |
| CACHE-004 | 1.5s | 7.0s | 2 | 2 | 0→1 | 0→0 | ✅ Fixed |

**Key Metrics**:
- **Repeated hypotheses eliminated**: 0 in ContextForge vs 1 in baseline (DB-002)
- **Correct diagnosis rate**: 80% ContextForge vs 20% baseline (simulated)
- **Context items → selected**: 19→8 (58% reduction)
- **Token budget utilization**: ~10% of 12k budget

**Say**: "ContextForge isn't about speed in this demo - it's about **correctness and focus**. Bob gets the right evidence, not all evidence."

---

## Key Talking Points

### Must Emphasize
1. **"Right context, not more context"** - Core value prop
2. **Rejected hypotheses persist** - Bob never re-investigates dead ends
3. **Provenance on everything** - Every piece of evidence is traceable
4. **Token budget enforcement** - Fits in any model's context window
5. **File-based handoff is intentional** - Works with ANY AI that reads files

### Be Honest About
1. **Bob integration is file-based** - Not programmatic API
2. **Baseline numbers are simulated** - Not from controlled experiment
3. **ContextForge pipeline takes ~7s** - Not instant (ingestion + ranking + compilation)
4. **Bob's diagnosis is simulated** - Human reads context to Bob in demo
4. **No programmatic Bob API** - File handoff is current reality

### Avoid Saying
- ❌ "Bob is integrated with ContextForge"
- ❌ "Subagents are orchestrated by ContextForge"
- ❌ "50% faster debugging proven"
- ❌ "Automatic context injection into Bob"
- ❌ "MCP integration working"

---

## Backup Plans

### If Bob 2.0 Unavailable
- Show generated `debugging_context.md` on screen
- Walk through what Bob WOULD see
- Emphasize: "Any AI that reads files can use this"

### If Pipeline Fails
- Have pre-generated `debugging_context.md` ready
- Explain: "Pipeline is deterministic - here's what it produces"

### If Questions About Bob API
- Reference `docs/BOB_INTEGRATION_REALITY.md`
- "We'd love programmatic integration when Bob exposes an API"

---

## Demo Checklist

- [ ] Demo-app running on localhost:8000
- [ ] ContextForge installed (`pip install -e .`)
- [ ] `debugging_context.md` pre-generated as backup
- [ ] Bob 2.0 installed and accessible
- [ ] Terminal large enough for split view
- [ ] Pre-generated `metrics.json` for metrics slide
- [ ] `docs/BOB_INTEGRATION_REALITY.md` printed for reference

---

## File Locations for Demo

```
ContextForge root/
├── debugging_context.md          # Generated live
├── eval/results_*.json           # Evaluation results
├── demo-app/
│   ├── auth/token.py             # AUTH-001 bug location
│   ├── tasks/service.py          # INT-005, DB-002 bugs
│   └── tests/                    # 32 passing tests
├── docs/
│   ├── BOB_INTEGRATION_REALITY.md
│   ├── JUDGE_DEMO.md             # This file
│   └── evaluation.md             # Updated with real results
└── scripts/
    ├── reset_bug.sh              # Reset any bug
    └── demo_auth_debug.sh        # Original demo script
```

---

*Demo script version: 2026-09-27*
*Based on: Actual evaluation run (eval/results_20260927_012856.json)*