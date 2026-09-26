"""End-to-end integration test for foundation."""

import tempfile
from pathlib import Path

import pytest

from contextforge import (
    ContextIR,
    ContextItem,
    ContextType,
    DebuggingState,
    DeterministicRanker,
    ItemStatus,
    Provenance,
    RejectedHypothesis,
    SimpleCompiler,
    SourceType,
    SQLiteStore,
)


def make_item(
    type_: ContextType,
    content: str,
    source: str = "test.py",
    source_type: SourceType = SourceType.FILE,
    importance: float = 0.5,
    freshness: float = 1.0,
    status: ItemStatus = ItemStatus.UNVERIFIED,
    task_id: str = "task-123",
) -> ContextItem:
    """Helper to create a test item."""
    prov = Provenance(
        source_type=source_type,
        source_id=source,
        observer="test",
        task_id=task_id,
    )
    return ContextItem(
        type=type_,
        content=content,
        source=source,
        importance=importance,
        freshness=freshness,
        status=status,
        provenance=prov,
    )


@pytest.fixture
def store() -> SQLiteStore:
    """Create a temporary SQLite store for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    store = SQLiteStore(db_path)
    store.initialize()
    yield store
    store.close()
    db_path.unlink(missing_ok=True)


def test_end_to_end_foundation(store: SQLiteStore) -> None:
    """Full integration test: create → store → retrieve → rank → compile → verify."""

    # 1. CREATE: Build context items and IR
    task_id = "debug-login-001"
    task_description = "Debug intermittent login failures"

    ir = ContextIR(task_id=task_id, task_description=task_description)

    # Add various context items
    ir.add_item(make_item(
        ContextType.TASK,
        "Users report intermittent login failures after 30 min of inactivity",
    ))
    ir.add_item(make_item(
        ContextType.EVIDENCE,
        "JWT tokens expire after 1 hour",
        status=ItemStatus.VERIFIED,
        importance=0.9,
    ))
    ir.add_item(make_item(
        ContextType.EVIDENCE,
        "Refresh token rotation not implemented",
        source="auth.py",
        status=ItemStatus.VERIFIED,
        importance=0.8,
    ))
    ir.add_item(make_item(
        ContextType.FILE,
        "JWT validation logic in auth.py:validate_token()",
        source="auth.py",
        importance=0.7,
    ))
    ir.add_item(make_item(
        ContextType.FILE,
        "Token refresh endpoint in auth.py:refresh()",
        source="auth.py",
        importance=0.6,
    ))
    ir.add_item(make_item(
        ContextType.HYPOTHESIS,
        "Token expiration too short for user workflow",
        importance=0.7,
    ))
    ir.add_item(make_item(
        ContextType.HYPOTHESIS,
        "Clock skew between services causing premature expiry",
        importance=0.5,
    ))
    ir.add_item(make_item(
        ContextType.EVIDENCE,
        "Clock sync verified via NTP - no skew detected",
        source="monitoring",
        source_type=SourceType.TOOL,
        status=ItemStatus.VERIFIED,
    ))
    ir.add_item(make_item(
        ContextType.FAILED_HYPOTHESIS,
        "Database connection pool exhaustion",
        status=ItemStatus.REJECTED,
    ))
    ir.add_item(make_item(
        ContextType.PROJECT_STATE,
        "Python 3.12, FastAPI, PyJWT 2.8",
        importance=0.4,
    ))

    # 2. STORE: Persist everything
    store.put_ir(ir)
    store.put_state(DebuggingState(
        task_id=task_id,
        task_description=task_description,
        current_hypothesis="Token expiration too short for user workflow",
    ))

    # 3. RETRIEVE: Get items back
    retrieved_ir = store.get_ir_by_task(task_id)
    assert retrieved_ir is not None
    assert retrieved_ir.task_id == task_id
    assert len(retrieved_ir.items) == 10

    # 4. RANK: Deterministic ranking
    ranker = DeterministicRanker()
    ranked_items = ranker.rank(retrieved_ir.items, task_id)

    # Verify ranking order: verified evidence with high importance first
    assert ranked_items[0].type == ContextType.EVIDENCE
    assert ranked_items[0].status == ItemStatus.VERIFIED
    assert ranked_items[0].importance >= 0.8

    # 5. COMPILE: Build context package
    compiler = SimpleCompiler()
    package = compiler.compile(retrieved_ir, ranked_items)

    # 6. VERIFY: Check output
    assert package.task_id == task_id
    assert package.total_tokens > 0
    assert package.total_tokens <= compiler.config.max_context_tokens
    assert len(package.sections) > 0

    # Check key sections exist
    section_titles = [s.title for s in package.sections]
    assert "TASK" in section_titles
    assert "VERIFIED EVIDENCE" in section_titles
    assert "RELEVANT FILES" in section_titles

    # Check markdown output
    markdown = package.to_markdown()
    assert "Debug intermittent login failures" in markdown
    assert "JWT tokens expire after 1 hour" in markdown
    assert "Refresh token rotation not implemented" in markdown
    assert "auth.py" in markdown

    # Check provenance summary
    assert package.provenance_summary["total_items"] == 10
    assert package.provenance_summary["by_source_type"]["file"] > 0
    assert package.provenance_summary["by_source_type"]["tool"] > 0
    assert package.provenance_summary["by_status"]["verified"] > 0
    assert package.provenance_summary["by_status"]["rejected"] > 0

    # Check debugging state persisted
    state = store.get_state(task_id)
    assert state is not None
    assert state.current_hypothesis == "Token expiration too short for user workflow"


def test_rejected_hypothesis_persistence(store: SQLiteStore) -> None:
    """Test that rejected hypotheses are stored and retrievable."""
    task_id = "test-rejected-001"

    ir = ContextIR(task_id=task_id, task_description="Test rejected hypotheses")
    ir.add_item(make_item(
        ContextType.HYPOTHESIS,
        "Wrong password",
        status=ItemStatus.REJECTED,
    ))
    ir.add_item(make_item(
        ContextType.HYPOTHESIS,
        "Database down",
        status=ItemStatus.REJECTED,
    ))

    store.put_ir(ir)

    # Add rejected hypothesis to debugging state
    state = DebuggingState(task_id=task_id, task_description="Test")
    state.add_rejected_hypothesis(RejectedHypothesis(
        hypothesis="Wrong password",
        investigation="Checked auth logs - no failed attempts",
        result="FALSE",
        evidence=["ev-1"],
        rejected_by="user1",
    ))
    state.add_rejected_hypothesis(RejectedHypothesis(
        hypothesis="Database down",
        investigation="DB metrics show healthy",
        result="FALSE",
        evidence=["ev-2"],
        rejected_by="user1",
    ))
    store.put_state(state)

    # Retrieve and verify
    retrieved_state = store.get_state(task_id)
    assert retrieved_state is not None
    assert len(retrieved_state.rejected_hypotheses) == 2
    assert retrieved_state.rejected_hypotheses[0].hypothesis == "Wrong password"
    assert retrieved_state.rejected_hypotheses[0].result == "FALSE"
    assert retrieved_state.rejected_hypotheses[1].hypothesis == "Database down"
