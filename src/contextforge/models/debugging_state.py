"""Debugging state model - session state for debugging tasks."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ActionType(StrEnum):
    """Type of action taken during debugging."""

    INVESTIGATE = "investigate"
    TEST = "test"
    MODIFY = "modify"
    VERIFY = "verify"
    DOCUMENT = "document"


class DebuggingStatus(StrEnum):
    """Current status of debugging session."""

    ACTIVE = "active"
    PAUSED = "paused"
    RESOLVED = "resolved"
    BLOCKED = "blocked"
    ABANDONED = "abandoned"


class RejectedHypothesis(BaseModel):
    """A hypothesis that was investigated and rejected."""

    hypothesis: str
    investigation: str
    result: str  # FALSE | INCONCLUSIVE | SUPERSEDED
    evidence: list[str] = Field(default_factory=list)  # ContextItem IDs
    rejected_at: datetime = Field(default_factory=datetime.utcnow)
    rejected_by: str = ""


class Action(BaseModel):
    """An action taken during debugging."""

    type: ActionType
    description: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    actor: str  # user | agent | tool
    result: str | None = None
    related_item_ids: list[str] = Field(default_factory=list)


class DebuggingState(BaseModel):
    """Session state for a debugging task."""

    task_id: str
    task_description: str
    current_hypothesis: str | None = None
    confirmed_facts: list[str] = Field(default_factory=list)  # ContextItem IDs
    evidence: list[str] = Field(default_factory=list)  # ContextItem IDs
    rejected_hypotheses: list[RejectedHypothesis] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    relevant_files: list[str] = Field(default_factory=list)  # ContextItem IDs
    previous_actions: list[Action] = Field(default_factory=list)
    status: DebuggingStatus = DebuggingStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_fact(self, item_id: str) -> None:
        """Add a confirmed fact."""
        if item_id not in self.confirmed_facts:
            self.confirmed_facts.append(item_id)
            self.updated_at = datetime.utcnow()

    def add_evidence(self, item_id: str) -> None:
        """Add evidence."""
        if item_id not in self.evidence:
            self.evidence.append(item_id)
            self.updated_at = datetime.utcnow()

    def add_rejected_hypothesis(self, hypothesis: RejectedHypothesis) -> None:
        """Add a rejected hypothesis."""
        self.rejected_hypotheses.append(hypothesis)
        self.updated_at = datetime.utcnow()

    def set_hypothesis(self, hypothesis: str) -> None:
        """Set current hypothesis."""
        self.current_hypothesis = hypothesis
        self.updated_at = datetime.utcnow()

    def add_open_question(self, question: str) -> None:
        """Add an open question."""
        if question not in self.open_questions:
            self.open_questions.append(question)
            self.updated_at = datetime.utcnow()

    def add_relevant_file(self, item_id: str) -> None:
        """Add a relevant file."""
        if item_id not in self.relevant_files:
            self.relevant_files.append(item_id)
            self.updated_at = datetime.utcnow()

    def record_action(self, action: Action) -> None:
        """Record an action."""
        self.previous_actions.append(action)
        self.updated_at = datetime.utcnow()

    def update_status(self, status: DebuggingStatus) -> None:
        """Update debugging status."""
        self.status = status
        self.updated_at = datetime.utcnow()


class ContextSection(BaseModel):
    """A section in the compiled context package."""

    title: str
    content: str
    priority: int = 0
    item_ids: list[str] = Field(default_factory=list)
    token_estimate: int = 0


class ContextPackage(BaseModel):
    """Compiled context package for agent consumption."""

    task_id: str
    task_description: str
    sections: list[ContextSection] = Field(default_factory=list)
    total_tokens: int = 0
    compiled_at: datetime = Field(default_factory=datetime.utcnow)
    provenance_summary: dict[str, Any] = Field(default_factory=dict)

    def to_markdown(self) -> str:
        """Render as markdown."""
        lines = [
            f"# Context Package: {self.task_description}",
            f"**Task ID:** {self.task_id}",
            f"**Compiled:** {self.compiled_at.isoformat()}",
            f"**Estimated Tokens:** {self.total_tokens}",
            "",
        ]

        for section in sorted(self.sections, key=lambda s: s.priority):
            lines.append(f"## {section.title}")
            lines.append(section.content)
            lines.append("")

        return "\n".join(lines)

    def to_json(self) -> str:
        """Serialize to JSON."""
        return self.model_dump_json(indent=2)
