"""Unit tests for DebuggingState model."""

from contextforge.models import (
    Action,
    ActionType,
    ContextPackage,
    ContextSection,
    DebuggingState,
    DebuggingStatus,
    RejectedHypothesis,
)


def test_debugging_state_creation() -> None:
    """Test basic DebuggingState creation."""
    state = DebuggingState(
        task_id="task-123",
        task_description="Debug login",
    )

    assert state.task_id == "task-123"
    assert state.task_description == "Debug login"
    assert state.current_hypothesis is None
    assert state.confirmed_facts == []
    assert state.evidence == []
    assert state.rejected_hypotheses == []
    assert state.open_questions == []
    assert state.relevant_files == []
    assert state.previous_actions == []
    assert state.status == DebuggingStatus.ACTIVE


def test_debugging_state_add_fact() -> None:
    """Test adding confirmed facts."""
    state = DebuggingState(task_id="task-123", task_description="Test")
    state.add_fact("item-1")
    state.add_fact("item-2")
    state.add_fact("item-1")  # Duplicate

    assert state.confirmed_facts == ["item-1", "item-2"]


def test_debugging_state_add_evidence() -> None:
    """Test adding evidence."""
    state = DebuggingState(task_id="task-123", task_description="Test")
    state.add_evidence("ev-1")
    state.add_evidence("ev-2")

    assert state.evidence == ["ev-1", "ev-2"]


def test_debugging_state_rejected_hypothesis() -> None:
    """Test adding rejected hypothesis."""
    state = DebuggingState(task_id="task-123", task_description="Test")
    rejected = RejectedHypothesis(
        hypothesis="JWT secret mismatch",
        investigation="Compared env config",
        result="FALSE",
        evidence=["ev-1"],
        rejected_by="user1",
    )
    state.add_rejected_hypothesis(rejected)

    assert len(state.rejected_hypotheses) == 1
    assert state.rejected_hypotheses[0].hypothesis == "JWT secret mismatch"
    assert state.rejected_hypotheses[0].result == "FALSE"


def test_debugging_state_set_hypothesis() -> None:
    """Test setting current hypothesis."""
    state = DebuggingState(task_id="task-123", task_description="Test")
    state.set_hypothesis("Token expiration issue")

    assert state.current_hypothesis == "Token expiration issue"


def test_debugging_state_open_questions() -> None:
    """Test adding open questions."""
    state = DebuggingState(task_id="task-123", task_description="Test")
    state.add_open_question("Why does token expire early?")
    state.add_open_question("Is clock skewed?")
    state.add_open_question("Why does token expire early?")  # Duplicate

    assert state.open_questions == ["Why does token expire early?", "Is clock skewed?"]


def test_debugging_state_relevant_files() -> None:
    """Test adding relevant files."""
    state = DebuggingState(task_id="task-123", task_description="Test")
    state.add_relevant_file("file-1")
    state.add_relevant_file("file-2")

    assert state.relevant_files == ["file-1", "file-2"]


def test_debugging_state_record_action() -> None:
    """Test recording actions."""
    state = DebuggingState(task_id="task-123", task_description="Test")
    action = Action(
        type=ActionType.INVESTIGATE,
        description="Checked JWT config",
        actor="user1",
        result="Found mismatch",
        related_item_ids=["item-1"],
    )
    state.record_action(action)

    assert len(state.previous_actions) == 1
    assert state.previous_actions[0].type == ActionType.INVESTIGATE


def test_debugging_state_update_status() -> None:
    """Test updating status."""
    state = DebuggingState(task_id="task-123", task_description="Test")
    state.update_status(DebuggingStatus.RESOLVED)

    assert state.status == DebuggingStatus.RESOLVED


def test_context_package_markdown() -> None:
    """Test ContextPackage markdown rendering."""
    pkg = ContextPackage(
        task_id="task-123",
        task_description="Debug login",
        sections=[
            ContextSection(
                title="CURRENT TASK",
                content="Debug login issue",
                priority=100,
                item_ids=["item-1"],
                token_estimate=50,
            ),
            ContextSection(
                title="VERIFIED EVIDENCE",
                content="- Token expires in 1 hour\n",
                priority=90,
                item_ids=["item-2"],
                token_estimate=30,
            ),
        ],
        total_tokens=80,
    )

    md = pkg.to_markdown()
    assert "# Context Package: Debug login" in md
    assert "## CURRENT TASK" in md
    assert "## VERIFIED EVIDENCE" in md
    assert "Debug login issue" in md
    assert "Token expires in 1 hour" in md


def test_context_package_json() -> None:
    """Test ContextPackage JSON serialization."""
    pkg = ContextPackage(
        task_id="task-123",
        task_description="Test",
        total_tokens=100,
    )

    json_str = pkg.to_json()
    assert isinstance(json_str, str)
    assert "task-123" in json_str
