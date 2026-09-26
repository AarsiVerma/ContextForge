"""Unit tests for DebuggingSession model."""

import pytest
from datetime import datetime

from contextforge.models import (
    DebuggingSession,
    SessionStatus,
    HypothesisRecord,
    ActionRecord,
    ContextPackageRecord,
)


def test_debugging_session_creation():
    """Test basic session creation."""
    session = DebuggingSession(
        task_id="task-123",
        task_description="Debug OAuth refresh",
    )

    assert session.task_id == "task-123"
    assert session.task_description == "Debug OAuth refresh"
    assert session.status == SessionStatus.ACTIVE
    assert session.hypotheses == []
    assert session.actions == []
    assert session.generated_packages == []


def test_add_hypothesis():
    """Test adding hypotheses."""
    session = DebuggingSession(task_id="task-123", task_description="Test")
    h1 = session.add_hypothesis("JWT secret mismatch", confidence=0.7)
    h2 = session.add_hypothesis("Token rotation race condition", confidence=0.5)

    assert len(session.hypotheses) == 2
    assert session.current_hypothesis_id == h2.id
    assert h1.status == "ACTIVE"
    assert h1.confidence == 0.7


def test_reject_hypothesis():
    """Test rejecting a hypothesis."""
    session = DebuggingSession(task_id="task-123", task_description="Test")
    h = session.add_hypothesis("Wrong password")

    result = session.reject_hypothesis(h.id, "Password verified in logs")

    assert result is True
    assert h.status == "REJECTED"
    assert h.rejected_reason == "Password verified in logs"
    assert h.rejected_at is not None


def test_confirm_hypothesis():
    """Test confirming a hypothesis."""
    session = DebuggingSession(task_id="task-123", task_description="Test")
    h = session.add_hypothesis("Token rotation race condition")

    result = session.confirm_hypothesis(h.id)

    assert result is True
    assert h.status == "CONFIRMED"


def test_get_active_hypotheses():
    """Test getting active hypotheses."""
    session = DebuggingSession(task_id="task-123", task_description="Test")
    session.add_hypothesis("H1")
    h2 = session.add_hypothesis("H2")
    session.add_hypothesis("H3")
    session.reject_hypothesis(h2.id, "Rejected")

    active = session.get_active_hypotheses()
    rejected = session.get_rejected_hypotheses()

    assert len(active) == 2
    assert len(rejected) == 1
    assert rejected[0].id == h2.id


def test_record_action():
    """Test recording actions."""
    session = DebuggingSession(task_id="task-123", task_description="Test")
    action = session.record_action(
        action_type="investigate",
        description="Checked JWT config",
        actor="user1",
        result="Found mismatch",
        related_item_ids=["item-1"],
    )

    assert len(session.actions) == 1
    assert action.type == "investigate"
    assert action.actor == "user1"
    assert action.result == "Found mismatch"


def test_record_package():
    """Test recording generated package."""
    session = DebuggingSession(task_id="task-123", task_description="Test")
    from contextforge.models import ContextPackage
    package = ContextPackage(task_id="task-123", task_description="Test", total_tokens=500)

    metrics = {
        "candidate_items": 20,
        "selected_items": 8,
        "discarded_items": 10,
        "duplicates_removed": 2,
        "estimated_tokens": 500,
        "budget": 8000,
        "compression_ratio": 0.4,
    }

    record = session.record_package(package, metrics)

    assert len(session.generated_packages) == 1
    assert record.candidate_items == 20
    assert record.selected_items == 8
    assert record.compression_ratio == 0.4


def test_update_status():
    """Test updating session status."""
    session = DebuggingSession(task_id="task-123", task_description="Test")
    session.update_status(SessionStatus.RESOLVED)

    assert session.status == SessionStatus.RESOLVED


def test_get_timeline():
    """Test getting chronological timeline."""
    session = DebuggingSession(task_id="task-123", task_description="Test")
    h = session.add_hypothesis("Test hypothesis")
    session.record_action("investigate", "Checked logs", "user1")
    session.reject_hypothesis(h.id, "False")

    timeline = session.get_timeline()

    assert len(timeline) == 3  # hypothesis_created, action, hypothesis_rejected
    # Check chronological order
    for i in range(len(timeline) - 1):
        assert timeline[i]["timestamp"] <= timeline[i + 1]["timestamp"]

    types = [e["type"] for e in timeline]
    assert "hypothesis_created" in types
    assert "action" in types
    assert "hypothesis_rejected" in types