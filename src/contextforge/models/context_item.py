"""ContextItem model - atomic unit of context."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from contextforge.models.provenance import Provenance, VerificationInfo


class ContextType(StrEnum):
    """Type of context item."""

    TASK = "task"
    FACT = "fact"
    EVIDENCE = "evidence"
    HYPOTHESIS = "hypothesis"
    FAILED_HYPOTHESIS = "failed_hypothesis"
    DECISION = "decision"
    FILE = "file"
    LOG = "log"
    TEST_RESULT = "test_result"
    TOOL_OUTPUT = "tool_output"
    CONSTRAINT = "constraint"
    PROJECT_STATE = "project_state"


class ItemStatus(StrEnum):
    """Verification status of a context item."""

    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class ContextItem(BaseModel):
    """Atomic unit of context with full provenance."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    type: ContextType
    content: str
    source: str
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    freshness: float = Field(default=1.0, ge=0.0, le=1.0)
    status: ItemStatus = ItemStatus.UNVERIFIED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    provenance: Provenance  # Forward reference
    tags: set[str] = Field(default_factory=set)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        """Update updated_at on modification."""
        self.updated_at = datetime.utcnow()

    def update_freshness(self, decay_hours: float = 24.0) -> None:
        """Decay freshness based on age."""
        age_hours = (datetime.utcnow() - self.created_at).total_seconds() / 3600
        if age_hours > decay_hours:
            self.freshness = max(0.0, 1.0 - (age_hours - decay_hours) / decay_hours)
        self.updated_at = datetime.utcnow()

    def mark_verified(self, verification_info: VerificationInfo) -> None:
        """Mark item as verified with verification info."""
        self.status = ItemStatus.VERIFIED
        self.provenance.verification = verification_info
        self.updated_at = datetime.utcnow()

    def mark_rejected(self, reason: str) -> None:
        """Mark item as rejected."""
        self.status = ItemStatus.REJECTED
        self.metadata["rejection_reason"] = reason
        self.updated_at = datetime.utcnow()

    def supersede(self, new_item_id: str) -> None:
        """Mark item as superseded by another."""
        self.status = ItemStatus.SUPERSEDED
        self.metadata["superseded_by"] = new_item_id
        self.updated_at = datetime.utcnow()
