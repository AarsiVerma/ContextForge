# ContextForge

Model-agnostic context management infrastructure for AI coding agents.

## Vision

> **Don't give the AI more context. Give it the right context.**

ContextForge captures, structures, retrieves, ranks, and compiles debugging context for AI coding agents — starting with IBM Bob 2.0.

## Status

**Milestone 3 complete** — IBM Bob 2.0 Hackathon MVP ready.

### Implemented (Milestone 3: Hackathon MVP)
- **Demo Application**: FastAPI "TaskFlow" with 5 reproducible debugging bugs
  - AUTH-001: Refresh token blacklist key mismatch (401 for valid tokens)
  - DB-002: Task assignment race condition (concurrent assignments succeed)
  - API-003: Invalid priority returns 500 instead of 422
  - INT-005: Pagination returns duplicates between pages
  - CACHE-004: Stale user permissions in JWT
- **Bob 2.0 Integration**: Research on Bob's modes, subagents, MCP, CLI, guardrails
- **Local Context Ranker Research**: Cross-encoder, FlashRank, BM25 evaluation
- **Demo Documentation**: Complete demo guide with run instructions
- **Evaluation Report**: Baseline experiment with measurable metrics
- **Security Validation**: Context injection threat model validated

### Implemented (Milestone 2: Evidence Pipeline)
- **Context Ingestion**: FileSource, TextSource, TaskSource, ToolOutputSource, TestResultSource
- **Normalization**: Type inference, importance scoring, provenance enrichment
- **Deterministic Retrieval**: Token overlap + metadata filtering
- **Deterministic Ranking**: 6 weighted signals (relevance, freshness, importance, verification, source reliability, task relationship)
- **Context Selection**: Token budget enforcement, priority preservation, deduplication
- **Debugging Sessions**: Hypothesis tracking (active/rejected/confirmed), action history, package generation history
- **Hypothesis Workflow**: Explicit states (ACTIVE/REJECTED/CONFIRMED), rejection persistence
- **Enhanced Compiler**: 12 sections, token budgeting, metrics, markdown/JSON output
- **Inspection/Debug Mode**: PipelineInspector, DebugContext for stage-by-stage observability
- **CLI**: `contextforge ingest|retrieve|rank|compile|pipeline`
- **Realistic OAuth Fixture**: Demonstrates useful vs noisy context separation
- **Security**: Context injection threat model validated

### Foundation (Milestone 1)
- Core data models (ContextItem, ContextIR, Provenance, DebuggingState)
- SQLite storage with ContextStore protocol
- DeterministicRanker baseline
- SimpleCompiler
- Unit + integration tests (106 tests passing)

## Installation

```bash
pip install -e .
```

## Development

```bash
pip install -e ".[dev]"
ruff check .
ruff format .
mypy src/contextforge
pytest
```

## Quick Start

```bash
# Run full pipeline on OAuth fixture
contextforge pipeline --path tests/fixtures/oauth_refresh/src --task-id oauth-001 --task-desc "OAuth refresh returns 401" --query "refresh token 401" --output package.md

# Run demo app pipeline
contextforge pipeline --path demo-app --task-id demo-001 --task-desc "Debug OAuth refresh 401" --query "refresh token 401" --output debugging_context.md
```

## Demo Application

```bash
# Start demo app
cd demo-app
python -m uvicorn main:app --reload --port 8000

# Run tests
python -m pytest tests/ -v
```

## Hackathon Demo

See [docs/demo.md](docs/demo.md) for complete demo instructions.

## License

MIT