# Context IR Specification

## Purpose

The Context Intermediate Representation (IR) is the **canonical, model-agnostic** representation of debugging context. It is:

- Independent of any AI model (Bob, GPT, Claude, etc.)
- Independent of any specific agent framework
- Serializable, inspectable, versionable, extensible
- Deterministic

## Entities

### ContextItem

Atomic unit of context.

```python
class ContextItem:
    id: str                    # UUID
    type: ContextType          # fact | evidence | hypothesis | decision | file | constraint | task
    content: str               # Human-readable content
    source: str                # Origin identifier (file path, tool name, user, etc.)
    importance: float          # 0.0-1.0, relative importance
    freshness: float           # 0.0-1.0, temporal relevance
    status: ItemStatus         # verified | unverified | rejected | superseded
    created_at: datetime
    updated_at: datetime
    provenance: Provenance     # Full origin trace
    tags: set[str]             # Arbitrary tags for retrieval
    metadata: dict[str, Any]   # Extensible extra fields
```

### ContextType

```python
class ContextType(Enum):
    TASK = "task"                    # Current debugging task
    FACT = "fact"                    # Verified truth
    EVIDENCE = "evidence"            # Supporting observation
    HYPOTHESIS = "hypothesis"        # Proposed explanation
    FAILED_HYPOTHESIS = "failed_hypothesis"  # Rejected hypothesis
    DECISION = "decision"            # Action taken or decision made
    FILE = "file"                    # Relevant source file
    CONSTRAINT = "constraint"        # Limitation or requirement
    PROJECT_STATE = "project_state"  # Project/config state snapshot
```

### ItemStatus

```python
class ItemStatus(Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
```

### Provenance

Complete origin trace for a context item.

```python
class Provenance:
    source_type: SourceType        # file | tool | user | agent | inference
    source_id: str                 # Specific identifier (path, tool name, etc.)
    observer: str                  # Who/what observed this
    timestamp: datetime            # When observed
    verification: VerificationInfo # How it was verified (if applicable)
    task_id: str | None            # Associated debugging task
    parent_ids: list[str]          # Derived from these items
    confidence: float              # 0.0-1.0 confidence in accuracy
```

### SourceType

```python
class SourceType(Enum):
    FILE = "file"              # Source code, config, docs
    TOOL = "tool"              # Linter, test runner, debugger, analyzer
    USER = "user"              # Human input
    AGENT = "agent"            # AI agent output
    INFERENCE = "inference"    # Derived by ContextForge logic
```

### VerificationInfo

```python
class VerificationInfo:
    method: str                # How verified (test, review, cross-ref, etc.)
    verified_by: str           # Who/what verified
    verified_at: datetime
    evidence_ids: list[str]    # Supporting evidence items
```

### DebuggingState

Session state for a debugging task.

```python
class DebuggingState:
    task_id: str
    task_description: str
    current_hypothesis: str | None
    confirmed_facts: list[str]           # ContextItem IDs
    evidence: list[str]                  # ContextItem IDs
    rejected_hypotheses: list[RejectedHypothesis]
    open_questions: list[str]
    relevant_files: list[str]            # ContextItem IDs (type=FILE)
    previous_actions: list[Action]
    status: DebuggingStatus
    created_at: datetime
    updated_at: datetime
```

### RejectedHypothesis

```python
class RejectedHypothesis:
    hypothesis: str
    investigation: str
    result: str                      # FALSE | INCONCLUSIVE | SUPERSEDED
    evidence: list[str]              # ContextItem IDs
    rejected_at: datetime
    rejected_by: str
```

### Action

```python
class Action:
    type: ActionType                 # investigate | test | modify | verify | document
    description: str
    timestamp: datetime
    actor: str                       # user | agent | tool
    result: str | None
    related_item_ids: list[str]
```

### ContextPackage

Output of the compiler — what the agent receives.

```python
class ContextPackage:
    task_id: str
    task_description: str
    sections: list[ContextSection]
    total_tokens: int
    compiled_at: datetime
    provenance_summary: ProvenanceSummary
```

### ContextSection

```python
class ContextSection:
    title: str
    content: str
    priority: int                    # Lower = higher priority
    item_ids: list[str]              # Source ContextItem IDs
    token_estimate: int
```

## Lifecycle

```
CREATE → STORE → RETRIEVE → RANK → COMPILE → DELIVER
  │                                            │
  └────────────── UPDATE (freshness, status) ──┘
```

Items can be updated (freshness decay, status change, new evidence).

## Versioning

- Context IR version tracked in `ContextIR.version` (semver)
- Breaking changes = major version
- Serialization includes version field
- Migration utilities for version upgrades

## Serialization

- Primary: JSON (inspectable, human-readable)
- Secondary: MessagePack (compact, for storage)
- Pydantic models handle (de)serialization
- All datetime fields: ISO 8601 UTC

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Flat item list in IR | Simple, queryable, no nested schema evolution pain |
| Provenance on every item | Non-negotiable for debugging trust |
| Rejected hypotheses retained | Prevents re-investigation loops |
| Deterministic ranking only | Baseline for ML comparison; no hidden behavior |
| JSON serialization | Inspectability > compactness for foundation |
| Pydantic models | Validation, serialization, IDE support out of box |