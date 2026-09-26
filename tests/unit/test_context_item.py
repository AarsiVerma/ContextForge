"""Unit tests for ContextItem model."""

from datetime import datetime

from contextforge.models import (
    ContextItem,
    ContextType,
    ItemStatus,
    Provenance,
    VerificationInfo,
)


def test_context_item_creation() -> None:
    """Test basic ContextItem creation."""
    provenance = Provenance.from_file("test.py", "user1", "task-123")
    item = ContextItem(
        type=ContextType.EVIDENCE,
        content="Test evidence",
        source="test.py",
        provenance=provenance,
    )

    assert item.id is not None
    assert item.type == ContextType.EVIDENCE
    assert item.content == "Test evidence"
    assert item.source == "test.py"
    assert item.importance == 0.5
    assert item.freshness == 1.0
    assert item.status == ItemStatus.UNVERIFIED
    assert isinstance(item.created_at, datetime)
    assert isinstance(item.updated_at, datetime)
    assert item.provenance == provenance
    assert item.tags == set()
    assert item.metadata == {}


def test_context_item_with_custom_values() -> None:
    """Test ContextItem with custom importance/freshness."""
    provenance = Provenance.from_tool("pytest", "agent", "task-123")
    item = ContextItem(
        type=ContextType.FACT,
        content="Custom fact",
        source="pytest",
        importance=0.9,
        freshness=0.8,
        provenance=provenance,
        tags={"critical", "auth"},
        metadata={"key": "value"},
    )

    assert item.importance == 0.9
    assert item.freshness == 0.8
    assert item.tags == {"critical", "auth"}
    assert item.metadata == {"key": "value"}


def test_context_item_mark_verified() -> None:
    """Test marking item as verified."""
    provenance = Provenance.from_file("test.py", "user1", "task-123")
    item = ContextItem(
        type=ContextType.EVIDENCE,
        content="Test",
        source="test.py",
        provenance=provenance,
    )

    verification = VerificationInfo(
        method="unit_test",
        verified_by="test_runner",
        evidence_ids=["ev-1"],
    )
    item.mark_verified(verification)

    assert item.status == ItemStatus.VERIFIED
    assert item.provenance.verification == verification


def test_context_item_mark_rejected() -> None:
    """Test marking item as rejected."""
    provenance = Provenance.from_file("test.py", "user1", "task-123")
    item = ContextItem(
        type=ContextType.HYPOTHESIS,
        content="Bad hypothesis",
        source="test.py",
        provenance=provenance,
    )

    item.mark_rejected("Contradicted by evidence")

    assert item.status == ItemStatus.REJECTED
    assert item.metadata["rejection_reason"] == "Contradicted by evidence"


def test_context_item_supersede() -> None:
    """Test marking item as superseded."""
    provenance = Provenance.from_file("test.py", "user1", "task-123")
    item = ContextItem(
        type=ContextType.FACT,
        content="Old fact",
        source="test.py",
        provenance=provenance,
    )

    item.supersede("new-item-id")

    assert item.status == ItemStatus.SUPERSEDED
    assert item.metadata["superseded_by"] == "new-item-id"


def test_context_item_update_freshness() -> None:
    """Test freshness decay."""
    provenance = Provenance.from_file("test.py", "user1", "task-123")
    item = ContextItem(
        type=ContextType.EVIDENCE,
        content="Test",
        source="test.py",
        provenance=provenance,
        freshness=1.0,
    )

    # Mock old creation time
    from datetime import timedelta
    item.created_at = datetime.utcnow() - timedelta(hours=48)

    item.update_freshness(decay_hours=24.0)

    assert item.freshness < 1.0
    assert item.freshness >= 0.0
