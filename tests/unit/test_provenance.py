"""Unit tests for Provenance model."""

from contextforge.models import (
    Provenance,
    SourceType,
    VerificationInfo,
)


def test_provenance_from_file() -> None:
    """Test creating provenance from file."""
    prov = Provenance.from_file("/path/to/file.py", "user1", "task-123")

    assert prov.source_type == SourceType.FILE
    assert prov.source_id == "/path/to/file.py"
    assert prov.observer == "user1"
    assert prov.task_id == "task-123"
    assert prov.confidence == 1.0
    assert prov.parent_ids == []


def test_provenance_from_tool() -> None:
    """Test creating provenance from tool."""
    prov = Provenance.from_tool("pytest", "agent", "task-123")

    assert prov.source_type == SourceType.TOOL
    assert prov.source_id == "pytest"
    assert prov.observer == "agent"
    assert prov.task_id == "task-123"


def test_provenance_from_user() -> None:
    """Test creating provenance from user."""
    prov = Provenance.from_user("user123", "task-123")

    assert prov.source_type == SourceType.USER
    assert prov.source_id == "user123"
    assert prov.observer == "user123"
    assert prov.task_id == "task-123"


def test_provenance_from_agent() -> None:
    """Test creating provenance from agent."""
    prov = Provenance.from_agent("bob-2.0", "task-123")

    assert prov.source_type == SourceType.AGENT
    assert prov.source_id == "bob-2.0"
    assert prov.observer == "bob-2.0"
    assert prov.task_id == "task-123"


def test_provenance_from_inference() -> None:
    """Test creating provenance from inference."""
    prov = Provenance.from_inference(
        "Derived from test failure",
        ["item-1", "item-2"],
        "task-123",
    )

    assert prov.source_type == SourceType.INFERENCE
    assert prov.source_id == "Derived from test failure"
    assert prov.observer == "contextforge"
    assert prov.task_id == "task-123"
    assert prov.parent_ids == ["item-1", "item-2"]
    assert prov.confidence == 0.8


def test_verification_info() -> None:
    """Test VerificationInfo model."""
    verif = VerificationInfo(
        method="cross_reference",
        verified_by="reviewer",
        evidence_ids=["ev-1", "ev-2"],
    )

    assert verif.method == "cross_reference"
    assert verif.verified_by == "reviewer"
    assert verif.evidence_ids == ["ev-1", "ev-2"]
