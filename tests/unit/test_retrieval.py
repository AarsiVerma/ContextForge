"""Unit tests for retrieval and selection."""

import pytest
import tempfile
from pathlib import Path

from contextforge import (
    ContextItem,
    ContextType,
    ItemStatus,
    ContextIR,
    Provenance,
    SourceType,
    SQLiteStore,
    LocalRetriever,
    DeterministicRetriever,
    ContextSelector,
    SelectionResult,
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
    """Create a temporary SQLite store."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    store = SQLiteStore(db_path)
    store.initialize()
    yield store
    store.close()
    db_path.unlink(missing_ok=True)


def test_deterministic_retriever_no_query(store: SQLiteStore):
    """Test retriever returns all items when no query."""
    # Add items
    items = [
        make_item(ContextType.EVIDENCE, "JWT token expires"),
        make_item(ContextType.FILE, "auth.py content", source="auth.py"),
        make_item(ContextType.LOG, "Error: timeout", source="app.log"),
    ]
    for item in items:
        store.put_item(item)

    retriever = DeterministicRetriever(store)
    results = retriever.retrieve(task_id="task-123", query=None)

    assert len(results) == 3


def test_deterministic_retriever_with_query(store: SQLiteStore):
    """Test retriever filters by query."""
    items = [
        make_item(ContextType.EVIDENCE, "JWT token expires in 30 minutes"),
        make_item(ContextType.FILE, "Database connection pool", source="db.py"),
        make_item(ContextType.LOG, "Error: Connection timeout", source="app.log"),
    ]
    for item in items:
        store.put_item(item)

    retriever = DeterministicRetriever(store)
    results = retriever.retrieve(task_id="task-123", query="JWT token")

    # Should find JWT-related items
    assert len(results) >= 1
    assert any("JWT" in item.content for item in results)


def test_deterministic_retriever_with_type_filter(store: SQLiteStore):
    """Test retriever filters by type."""
    items = [
        make_item(ContextType.EVIDENCE, "Evidence 1"),
        make_item(ContextType.FILE, "File 1", source="file1.py"),
        make_item(ContextType.LOG, "Log 1", source="app.log"),
    ]
    for item in items:
        store.put_item(item)

    retriever = DeterministicRetriever(store)
    results = retriever.retrieve(task_id="task-123", types=["evidence", "log"])

    assert len(results) == 2
    types = {item.type.value for item in results}
    assert types == {"evidence", "log"}


def test_local_retriever(store: SQLiteStore):
    """Test LocalRetriever wrapper."""
    items = [
        make_item(ContextType.EVIDENCE, "Test evidence"),
    ]
    for item in items:
        store.put_item(item)

    retriever = LocalRetriever(store)
    results = retriever.retrieve(task_id="task-123")

    assert len(results) == 1


def test_context_selector_basic(store: SQLiteStore):
    """Test basic selection under budget."""
    items = [
        make_item(ContextType.EVIDENCE, "High importance evidence", importance=0.9, status=ItemStatus.VERIFIED),
        make_item(ContextType.EVIDENCE, "Low importance evidence", importance=0.2),
        make_item(ContextType.FILE, "Relevant file", source="auth.py", importance=0.7),
    ]
    for item in items:
        store.put_item(item)

    selector = ContextSelector(max_tokens=1000)
    selection = selector.select(items, "task-123")

    assert isinstance(selection, SelectionResult)
    assert selection.metrics["selected_items"] >= 1
    assert selection.metrics["selected_items"] <= len(items)
    assert selection.metrics["estimated_tokens"] <= 1000


def test_context_selector_deduplication():
    """Test selector removes duplicates."""
    # Create items with same source and content (duplicates)
    prov1 = Provenance(source_type=SourceType.FILE, source_id="test.py", observer="test", task_id="task-123")
    prov2 = Provenance(source_type=SourceType.FILE, source_id="test.py", observer="test", task_id="task-123")
    prov3 = Provenance(source_type=SourceType.FILE, source_id="test.py", observer="test", task_id="task-123")

    item1 = ContextItem(type=ContextType.EVIDENCE, content="Same content", source="test.py", provenance=prov1, id="item-1")
    item2 = ContextItem(type=ContextType.EVIDENCE, content="Same content", source="test.py", provenance=prov2, id="item-2")
    item3 = ContextItem(type=ContextType.EVIDENCE, content="Different content", source="test.py", provenance=prov3, id="item-3")

    items = [item1, item2, item3]

    selector = ContextSelector(max_tokens=1000)
    selection = selector.select(items, "task-123")

    assert selection.metrics["duplicates_removed"] == 1
    assert selection.metrics["unique_items"] == 2


def test_context_selector_priority_verified():
    """Test selector prioritizes verified items."""
    items = [
        make_item(ContextType.EVIDENCE, "Unverified", importance=0.5, status=ItemStatus.UNVERIFIED),
        make_item(ContextType.EVIDENCE, "Verified", importance=0.5, status=ItemStatus.VERIFIED),
    ]

    selector = ContextSelector(max_tokens=1000)
    selection = selector.select(items, "task-123")

    # Verified should be selected first
    assert len(selection.selected) >= 1
    if len(selection.selected) == 1:
        assert selection.selected[0].status == ItemStatus.VERIFIED


def test_context_selector_budget_enforcement():
    """Test selector respects token budget."""
    # Create items with lots of content
    items = [
        make_item(ContextType.EVIDENCE, "x" * 5000, importance=0.9),  # ~1250 tokens
        make_item(ContextType.EVIDENCE, "y" * 5000, importance=0.8),
        make_item(ContextType.EVIDENCE, "z" * 5000, importance=0.7),
    ]

    selector = ContextSelector(max_tokens=1000)  # Only ~1000 tokens
    selection = selector.select(items, "task-123")

    assert selection.metrics["estimated_tokens"] <= 1000
    assert selection.metrics["selected_items"] < len(items)
    assert selection.metrics["discarded_items"] > 0


def test_context_selector_compression_ratio():
    """Test compression ratio calculation."""
    items = [
        make_item(ContextType.EVIDENCE, "Item 1"),
        make_item(ContextType.EVIDENCE, "Item 2"),
        make_item(ContextType.EVIDENCE, "Item 3"),
    ]

    selector = ContextSelector(max_tokens=1000)
    selection = selector.select(items, "task-123")

    assert "compression_ratio" in selection.metrics
    assert 0 <= selection.metrics["compression_ratio"] <= 1