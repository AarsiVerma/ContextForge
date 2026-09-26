"""Debugging session model for tracking complete debugging workflows."""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from contextforge.models import ContextIR, ContextPackage


class SessionStatus(StrEnum):
    """Status of a debugging session."""

    ACTIVE = "active"
    PAUSED = "paused"
    RESOLVED = "resolved"
    ABANDONED = "abandoned"


class HypothesisRecord(BaseModel):
    """Record of a hypothesis in the debugging session."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    hypothesis: str
    status: str  # ACTIVE, REJECTED, CONFIRMED
    evidence_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    rejected_at: datetime | None = None
    rejected_reason: str | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class ActionRecord(BaseModel):
    """Record of an action taken during debugging."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    type: str  # investigate, test, modify, verify, document
    description: str
    actor: str  # user, agent, tool
    result: str | None = None
    related_item_ids: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ContextPackageRecord(BaseModel):
    """Record of a generated context package."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    package_id: str
    task_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    candidate_items: int = 0
    selected_items: int = 0
    discarded_items: int = 0
    duplicates_removed: int = 0
    estimated_tokens: int = 0
    budget: int = 0
    compression_ratio: float = 0.0


class DebuggingSession(BaseModel):
    """Complete debugging session tracking all context, hypotheses, and actions."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    task_id: str
    task_description: str
    project_path: str | None = None
    status: SessionStatus = SessionStatus.ACTIVE

    # Core context
    context_ir_id: str | None = None
    current_context_ir: ContextIR | None = None

    # Hypotheses tracking
    hypotheses: list[HypothesisRecord] = Field(default_factory=list)
    current_hypothesis_id: str | None = None

    # Actions taken
    actions: list[ActionRecord] = Field(default_factory=list)

    # Generated context packages
    generated_packages: list[ContextPackageRecord] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_hypothesis(self, hypothesis: str, confidence: float = 0.5) -> HypothesisRecord:
        """Add a new hypothesis."""
        record = HypothesisRecord(hypothesis=hypothesis, status="ACTIVE", confidence=confidence)
        self.hypotheses.append(record)
        self.current_hypothesis_id = record.id
        self.updated_at = datetime.utcnow()
        return record

    def reject_hypothesis(self, hypothesis_id: str, reason: str) -> bool:
        """Mark a hypothesis as rejected."""
        for h in self.hypotheses:
            if h.id == hypothesis_id:
                h.status = "REJECTED"
                h.rejected_at = datetime.utcnow()
                h.rejected_reason = reason
                self.updated_at = datetime.utcnow()
                return True
        return False

    def confirm_hypothesis(self, hypothesis_id: str) -> bool:
        """Mark a hypothesis as confirmed."""
        for h in self.hypotheses:
            if h.id == hypothesis_id:
                h.status = "CONFIRMED"
                self.updated_at = datetime.utcnow()
                return True
        return False

    def get_active_hypotheses(self) -> list[HypothesisRecord]:
        """Get all active hypotheses."""
        return [h for h in self.hypotheses if h.status == "ACTIVE"]

    def get_rejected_hypotheses(self) -> list[HypothesisRecord]:
        """Get all rejected hypotheses."""
        return [h for h in self.hypotheses if h.status == "REJECTED"]

    def record_action(
        self,
        action_type: str,
        description: str,
        actor: str,
        result: str | None = None,
        related_item_ids: list[str] | None = None,
    ) -> ActionRecord:
        """Record an action taken during debugging."""
        action = ActionRecord(
            type=action_type,
            description=description,
            actor=actor,
            result=result,
            related_item_ids=related_item_ids or [],
        )
        self.actions.append(action)
        self.updated_at = datetime.utcnow()
        return action

    def record_package(self, package: ContextPackage, selection_metrics: dict[str, Any]) -> ContextPackageRecord:
        """Record a generated context package."""
        record = ContextPackageRecord(
            package_id=package.task_id,
            task_id=self.task_id,
            candidate_items=selection_metrics.get("candidate_items", 0),
            selected_items=selection_metrics.get("selected_items", 0),
            discarded_items=selection_metrics.get("discarded_items", 0),
            duplicates_removed=selection_metrics.get("duplicates_removed", 0),
            estimated_tokens=selection_metrics.get("estimated_tokens", 0),
            budget=selection_metrics.get("budget", 0),
            compression_ratio=selection_metrics.get("compression_ratio", 0.0),
        )
        self.generated_packages.append(record)
        self.updated_at = datetime.utcnow()
        return record

    def update_status(self, status: SessionStatus) -> None:
        """Update session status."""
        self.status = status
        self.updated_at = datetime.utcnow()

    def get_timeline(self) -> list[dict[str, Any]]:
        """Get a chronological timeline of all session events."""
        events: list[dict[str, Any]] = []

        for h in self.hypotheses:
            events.append({
                "timestamp": h.created_at,
                "type": "hypothesis_created",
                "description": f"Hypothesis: {h.hypothesis}",
                "details": {"id": h.id, "confidence": h.confidence},
            })
            if h.rejected_at:
                events.append({
                    "timestamp": h.rejected_at,
                    "type": "hypothesis_rejected",
                    "description": f"Rejected: {h.hypothesis}",
                    "details": {"id": h.id, "reason": h.rejected_reason},
                })

        for a in self.actions:
            events.append({
                "timestamp": a.timestamp,
                "type": "action",
                "description": f"{a.type}: {a.description}",
                "details": {"id": a.id, "actor": a.actor, "result": a.result},
            })

        for p in self.generated_packages:
            events.append({
                "timestamp": p.generated_at,
                "type": "package_generated",
                "description": f"Context package generated ({p.selected_items} items, {p.estimated_tokens} tokens)",
                "details": {"id": p.id, "metrics": p.model_dump()},
            })

        events.sort(key=lambda e: e["timestamp"])
        return events