"""Provenance model - origin tracking for context items."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class SourceType(StrEnum):
    """Origin type of a context item."""

    FILE = "file"
    TOOL = "tool"
    USER = "user"
    AGENT = "agent"
    INFERENCE = "inference"


class VerificationInfo(BaseModel):
    """Information about how an item was verified."""

    method: str = ""
    verified_by: str = ""
    verified_at: datetime = Field(default_factory=datetime.utcnow)
    evidence_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Provenance(BaseModel):
    """Complete origin trace for a context item."""

    source_type: SourceType
    source_id: str
    observer: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    verification: VerificationInfo = Field(default_factory=VerificationInfo)
    task_id: str | None = None
    parent_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_file(cls, file_path: str, observer: str, task_id: str | None = None) -> "Provenance":
        """Create provenance for a file source."""
        return cls(
            source_type=SourceType.FILE,
            source_id=file_path,
            observer=observer,
            task_id=task_id,
        )

    @classmethod
    def from_tool(cls, tool_name: str, observer: str, task_id: str | None = None) -> "Provenance":
        """Create provenance for a tool source."""
        return cls(
            source_type=SourceType.TOOL,
            source_id=tool_name,
            observer=observer,
            task_id=task_id,
        )

    @classmethod
    def from_user(cls, user_id: str, task_id: str | None = None) -> "Provenance":
        """Create provenance for a user source."""
        return cls(
            source_type=SourceType.USER,
            source_id=user_id,
            observer=user_id,
            task_id=task_id,
        )

    @classmethod
    def from_agent(cls, agent_name: str, task_id: str | None = None) -> "Provenance":
        """Create provenance for an agent source."""
        return cls(
            source_type=SourceType.AGENT,
            source_id=agent_name,
            observer=agent_name,
            task_id=task_id,
        )

    @classmethod
    def from_inference(
        cls,
        inference_description: str,
        parent_ids: list[str],
        task_id: str | None = None,
    ) -> "Provenance":
        """Create provenance for an inferred item."""
        return cls(
            source_type=SourceType.INFERENCE,
            source_id=inference_description,
            observer="contextforge",
            task_id=task_id,
            parent_ids=parent_ids,
            confidence=0.8,
        )
