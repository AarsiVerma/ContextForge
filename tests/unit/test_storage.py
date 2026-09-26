"""Unit tests for SQLite storage."""

import tempfile
from pathlib import Path

import pytest

from contextforge.models import (
    Action,
    ActionType,
    ContextIR,
    ContextItem,
    ContextType,
    DebuggingState,
    DebuggingStatus,
    ItemStatus,
    Provenance,
    RejectedHypothesis,
)
from contextforge.storage import SQLiteStore


def make_item(type_: ContextType, content: str, task_id: str = "task-123") -> ContextItem:
    """Helper to create a test item."""
    prov = Provenance.from_file("test.py", "user1", task_id)
    return ContextItem(type=type_, content=content, source="test.py", provenance=prov)


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


def test_store_put_and_get_item(store: SQLiteStore) -> None:
    """Test storing and retrieving a context item."""
    item = make_item(ContextType.EVIDENCE, "Test evidence")

    store.put_item(item)
    retrieved = store.get_item(item.id)

    assert retrieved is not None
    assert retrieved.id == item.id
    assert retrieved.type == item.type
    assert retrieved.content == item.content
    assert retrieved.source == item.source
    assert retrieved.importance == item.importance
    assert retrieved.freshness == item.freshness
    assert retrieved.status == item.status


def test_store_delete_item(store: SQLiteStore) -> None:
    """Test deleting a context item."""
    item = make_item(ContextType.EVIDENCE, "Test")
    store.put_item(item)

    deleted = store.delete_item(item.id)
    assert deleted is True

    retrieved = store.get_item(item.id)
    assert retrieved is None

    # Deleting non-existent returns False
    deleted = store.delete_item("non-existent")
    assert deleted is False


def test_store_list_items(store: SQLiteStore) -> None:
    """Test listing items with filters."""
    store.put_item(make_item(ContextType.EVIDENCE, "Evidence 1"))
    store.put_item(make_item(ContextType.FACT, "Fact 1"))
    store.put_item(make_item(ContextType.EVIDENCE, "Evidence 2"))
    store.put_item(make_item(ContextType.HYPOTHESIS, "Hypothesis"))

    all_items = store.list_items()
    assert len(all_items) == 4

    evidence = store.list_items(type_=ContextType.EVIDENCE.value)
    assert len(evidence) == 2

    facts = store.list_items(type_=ContextType.FACT.value)
    assert len(facts) == 1


def test_store_list_items_by_status(store: SQLiteStore) -> None:
    """Test listing items by status."""
    item1 = make_item(ContextType.EVIDENCE, "Verified")
    item1.status = ItemStatus.VERIFIED
    item2 = make_item(ContextType.EVIDENCE, "Unverified")
    item3 = make_item(ContextType.EVIDENCE, "Rejected")
    item3.status = ItemStatus.REJECTED

    store.put_item(item1)
    store.put_item(item2)
    store.put_item(item3)

    verified = store.list_items(status=ItemStatus.VERIFIED.value)
    assert len(verified) == 1
    assert verified[0].content == "Verified"

    unverified = store.list_items(status=ItemStatus.UNVERIFIED.value)
    assert len(unverified) == 1


def test_store_list_items_by_task(store: SQLiteStore) -> None:
    """Test listing items by task."""
    store.put_item(make_item(ContextType.EVIDENCE, "Task 1", "task-1"))
    store.put_item(make_item(ContextType.EVIDENCE, "Task 2", "task-2"))
    store.put_item(make_item(ContextType.FACT, "Task 1 also", "task-1"))

    task1_items = store.list_items(task_id="task-1")
    assert len(task1_items) == 2

    task2_items = store.list_items(task_id="task-2")
    assert len(task2_items) == 1


def test_store_context_ir(store: SQLiteStore) -> None:
    """Test storing and retrieving ContextIR."""
    ir = ContextIR(task_id="task-123", task_description="Test task")
    ir.add_item(make_item(ContextType.EVIDENCE, "Evidence 1"))
    ir.add_item(make_item(ContextType.FACT, "Fact 1"))

    store.put_ir(ir)

    retrieved = store.get_ir(ir.id)
    assert retrieved is not None
    assert retrieved.id == ir.id
    assert retrieved.task_id == ir.task_id
    assert retrieved.task_description == ir.task_description
    assert len(retrieved.items) == 2


def test_store_get_ir_by_task(store: SQLiteStore) -> None:
    """Test retrieving ContextIR by task ID."""
    ir = ContextIR(task_id="task-123", task_description="Test task")
    ir.add_item(make_item(ContextType.EVIDENCE, "Evidence"))

    store.put_ir(ir)

    retrieved = store.get_ir_by_task("task-123")
    assert retrieved is not None
    assert retrieved.task_id == "task-123"


def test_store_debugging_state(store: SQLiteStore) -> None:
    """Test storing and retrieving debugging state."""
    state = DebuggingState(
        task_id="task-123",
        task_description="Debug login",
    )
    state.add_fact("fact-1")
    state.add_evidence("ev-1")
    state.set_hypothesis("Token issue")
    state.add_rejected_hypothesis(RejectedHypothesis(
        hypothesis="Wrong password",
        investigation="Checked logs",
        result="FALSE",
        evidence=["ev-1"],
        rejected_by="user1",
    ))
    state.record_action(Action(
        type=ActionType.INVESTIGATE,
        description="Checked JWT config",
        actor="user1",
    ))
    state.update_status(DebuggingStatus.ACTIVE)

    store.put_state(state)

    retrieved = store.get_state("task-123")
    assert retrieved is not None
    assert retrieved.task_id == "task-123"
    assert retrieved.task_description == "Debug login"
    assert retrieved.confirmed_facts == ["fact-1"]
    assert retrieved.evidence == ["ev-1"]
    assert retrieved.current_hypothesis == "Token issue"
    assert len(retrieved.rejected_hypotheses) == 1
    assert retrieved.rejected_hypotheses[0].hypothesis == "Wrong password"
    assert len(retrieved.previous_actions) == 1
    assert retrieved.status == DebuggingStatus.ACTIVE


def test_store_delete_state(store: SQLiteStore) -> None:
    """Test deleting debugging state."""
    state = DebuggingState(task_id="task-123", task_description="Test")
    store.put_state(state)

    deleted = store.delete_state("task-123")
    assert deleted is True

    retrieved = store.get_state("task-123")
    assert retrieved is None

    deleted = store.delete_state("non-existent")
    assert deleted is False
