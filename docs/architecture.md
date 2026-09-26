# ContextForge Architecture

## System Boundaries

ContextForge is a **local, single-user library** for managing debugging context. It does not:
- Provide network services
- Implement authentication/authorization
- Run AI models
- Manage user accounts

It integrates with AI coding agents (starting with IBM Bob 2.0) by providing a context package they can consume.

## Major Components (Milestone 2)

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

### Models (`src/contextforge/models/`)

| Module | Responsibility |
|--------|----------------|
| `context_item.py` | Atomic context unit with id, type, content, metadata, provenance |
| `context_ir.py` | Canonical intermediate representation |
| `provenance.py` | Origin tracking for every context item |
| `debugging_state.py` | Debugging session state (hypotheses, facts, evidence) |
| `session.py` | DebuggingSession — complete workflow tracking (hypotheses, actions, packages) |

### Storage (`src/contextforge/storage/`)

| Module | Responsibility |
|--------|----------------|
| `base.py` | `ContextStore` protocol — CRUD + query |
| `sqlite.py` | SQLite implementation using `sqlite-utils` |

### Ingestion (`src/contextforge/ingestion/`)

| Module | Responsibility |
|--------|----------------|
| `base.py` | `ContextSource` protocol — standardize input from files, logs, tools, APIs |
| `sources.py` | Concrete sources: `FileSource`, `TextSource`, `TaskSource`, `ToolOutputSource`, `TestResultSource` |
| `normalize.py` | `Normalizer` — convert raw sources to structured ContextItems |

### Retrieval (`src/contextforge/retrieval/`)

| Module | Responsibility |
|--------|----------------|
| `base.py` | `ContextRetriever` protocol — fetch relevant items by task, type, tags |
| `local.py` | `DeterministicRetriever`, `LocalRetriever` — token overlap + metadata filtering |
| `selector.py` | `ContextSelector` — budget enforcement, priority preservation, deduplication |

### Ranking (`src/contextforge/ranking/`)

| Module | Responsibility |
|--------|----------------|
| `base.py` | `ContextRanker` protocol + `DeterministicRanker` — 6 weighted signals (relevance 30%, freshness 20%, importance 20%, verification 15%, source reliability 10%, task relationship 5%) |

### Compilation (`src/contextforge/compilation/`)

| Module | Responsibility |
|--------|----------------|
| `base.py` | `ContextCompiler` protocol + `SimpleCompiler` — deterministic compilation with token budget, multiple sections, metrics |

### Inspection (`src/contextforge/inspection.py`)

| Module | Responsibility |
|--------|----------------|
| `inspection.py` | `PipelineInspector`, `DebugContext` — stage-by-stage pipeline observability |

### CLI (`src/contextforge/cli.py`)

| Command | Description |
|---------|-------------|
| `ingest` | Ingest context from file sources |
| `retrieve` | Retrieve relevant context for a task |
| `rank` | Rank context items by relevance |
| `compile` | Compile context package |
| `pipeline` | Run full end-to-end pipeline |

## Data Flow (Milestone 2)

1. **Source** emits raw context (file, log, tool output, user input)
2. **Ingestion** (`ContextSource.fetch()`) produces raw ContextItems
3. **Normalization** (`Normalizer`) enriches items with types, provenance, importance
4. **Store** persists items, indexed for retrieval
5. **Retriever** fetches candidate items for a task (token overlap + metadata filters)
6. **Ranker** scores items deterministically (6 weighted signals)
7. **Selector** chooses items under token budget (priority preservation + deduplication)
8. **Compiler** builds final `ContextPackage` (sections, provenance, metrics)
9. **Inspector** records each stage for observability

## Context IR

See `docs/context-ir.md` for the canonical representation.

## Interfaces (Protocols)

All major components use Python `Protocol` for structural subtyping:
- `ContextStore`
- `ContextRetriever`
- `ContextRanker`
- `ContextCompiler`
- `ContextSource`

This enables:
- Easy testing with fakes/mocks
- Swappable backends (SQLite → PostgreSQL, local → vector)
- Clear extension points

## Future Extension Points

| Current | Future |
|---------|--------|
| SQLite | PostgreSQL, cloud SQL |
| Local retrieval | Vector/semantic search (FAISS, pgvector) |
| Deterministic ranker | Learned Context Intelligence Model |
| Local execution | Remote context service |
| Bob integration | Multi-agent support (Cursor, Copilot, etc.) |
| Single compiler | Model-specific compilation (token budgets, format) |

## Bob Integration Boundary

Bob 2.0 integration is **out of scope for foundation**. The boundary is:
- ContextForge produces `ContextPackage` (markdown/JSON)
- Bob consumes package via its context API
- No Bob-specific code in ContextForge core

## JEV Integration Boundary

JEV (Just-in-Time Environment Validation) is a future milestone. Boundary:
- ContextForge provides structured context
- JEV validates environment state against context
- No JEV dependencies in foundation

## Milestone 2 Achievements

- **Real context ingestion** from files, logs, tool output, developer tasks
- **Normalization layer** with type inference and importance scoring
- **Deterministic retrieval** with token overlap and metadata filtering
- **Deterministic ranking** with 6 weighted signals (baseline for ML comparison)
- **Context selection** with token budget enforcement and priority preservation
- **Deduplication** by source+content similarity
- **Debugging sessions** with hypothesis tracking and action history
- **Hypothesis workflow** with rejection persistence
- **Enhanced compiler** with 12 sections, token budgeting, metrics
- **Inspection/debug mode** for pipeline observability
- **CLI** for end-to-end pipeline execution
- **Realistic OAuth fixture** demonstrating useful vs noisy context separation
- **Security boundary** validated: malicious content treated as data only