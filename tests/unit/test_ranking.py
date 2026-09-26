"""Unit tests for deterministic ranking."""

from contextforge.models import (
    ContextItem,
    ContextType,
    ItemStatus,
    Provenance,
    SourceType,
)
from contextforge.ranking import DeterministicRanker


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


def test_ranker_basic() -> None:
    """Test basic ranking."""
    ranker = DeterministicRanker()
    items = [
        make_item(ContextType.EVIDENCE, "Low importance", importance=0.2),
        make_item(ContextType.EVIDENCE, "High importance", importance=0.9),
        make_item(ContextType.EVIDENCE, "Medium importance", importance=0.5),
    ]

    ranked = ranker.rank(items, "task-123")

    assert ranked[0].importance == 0.9
    assert ranked[1].importance == 0.5
    assert ranked[2].importance == 0.2


def test_ranker_freshness() -> None:
    """Test freshness affects ranking."""
    ranker = DeterministicRanker()
    items = [
        make_item(ContextType.EVIDENCE, "Old", freshness=0.2),
        make_item(ContextType.EVIDENCE, "New", freshness=1.0),
        make_item(ContextType.EVIDENCE, "Medium", freshness=0.6),
    ]

    ranked = ranker.rank(items, "task-123")

    assert ranked[0].freshness == 1.0
    assert ranked[1].freshness == 0.6
    assert ranked[2].freshness == 0.2


def test_ranker_verification_status() -> None:
    """Test verification status affects ranking."""
    ranker = DeterministicRanker()
    items = [
        make_item(ContextType.EVIDENCE, "Rejected", status=ItemStatus.REJECTED),
        make_item(ContextType.EVIDENCE, "Verified", status=ItemStatus.VERIFIED),
        make_item(ContextType.EVIDENCE, "Unverified", status=ItemStatus.UNVERIFIED),
    ]

    ranked = ranker.rank(items, "task-123")

    assert ranked[0].status == ItemStatus.VERIFIED
    assert ranked[1].status == ItemStatus.UNVERIFIED
    assert ranked[2].status == ItemStatus.REJECTED


def test_ranker_source_reliability() -> None:
    """Test source reliability affects ranking."""
    ranker = DeterministicRanker()
    items = [
        make_item(ContextType.EVIDENCE, "Inference", source_type=SourceType.INFERENCE),
        make_item(ContextType.EVIDENCE, "File", source_type=SourceType.FILE),
        make_item(ContextType.EVIDENCE, "Tool", source_type=SourceType.TOOL),
        make_item(ContextType.EVIDENCE, "Agent", source_type=SourceType.AGENT),
    ]

    ranked = ranker.rank(items, "task-123")

    # FILE > TOOL > AGENT > INFERENCE
    assert ranked[0].provenance.source_type == SourceType.FILE
    assert ranked[1].provenance.source_type == SourceType.TOOL
    assert ranked[2].provenance.source_type == SourceType.AGENT
    assert ranked[3].provenance.source_type == SourceType.INFERENCE


def test_ranker_task_relationship() -> None:
    """Test same-task items ranked higher."""
    ranker = DeterministicRanker()
    items = [
        make_item(ContextType.EVIDENCE, "Other task", task_id="other-task"),
        make_item(ContextType.EVIDENCE, "Same task", task_id="task-123"),
    ]

    ranked = ranker.rank(items, "task-123")

    assert ranked[0].provenance.task_id == "task-123"
    assert ranked[1].provenance.task_id == "other-task"


def test_ranker_relevance_query() -> None:
    """Test query relevance affects ranking."""
    ranker = DeterministicRanker()
    items = [
        make_item(ContextType.EVIDENCE, "JWT token validation failed"),
        make_item(ContextType.EVIDENCE, "Database connection timeout"),
        make_item(ContextType.EVIDENCE, "User login authentication error"),
    ]

    ranked = ranker.rank(items, "task-123", query="JWT authentication")

    # Items with JWT/authentication terms should rank higher
    assert "JWT" in ranked[0].content or "authentication" in ranked[0].content.lower()


def test_ranker_empty_list() -> None:
    """Test ranking empty list."""
    ranker = DeterministicRanker()
    ranked = ranker.rank([], "task-123")
    assert ranked == []


def test_ranker_single_item() -> None:
    """Test ranking single item."""
    ranker = DeterministicRanker()
    item = make_item(ContextType.EVIDENCE, "Single")
    ranked = ranker.rank([item], "task-123")
    assert ranked == [item]
