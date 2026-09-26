"""Core data models for ContextForge."""

from contextforge.models.context_ir import ContextIR
from contextforge.models.context_item import ContextItem, ContextType, ItemStatus
from contextforge.models.debugging_state import (
    Action,
    ActionType,
    ContextPackage,
    ContextSection,
    DebuggingState,
    DebuggingStatus,
    RejectedHypothesis,
)
from contextforge.models.provenance import Provenance, SourceType, VerificationInfo
from contextforge.models.session import (
    DebuggingSession,
    HypothesisRecord,
    ActionRecord,
    ContextPackageRecord,
    SessionStatus,
)

# Rebuild models to resolve forward references
ContextItem.model_rebuild()
ContextIR.model_rebuild()
DebuggingState.model_rebuild()
ContextPackage.model_rebuild()
ContextSection.model_rebuild()
DebuggingSession.model_rebuild()

__all__ = [
    "ContextItem",
    "ContextType",
    "ItemStatus",
    "ContextIR",
    "Provenance",
    "SourceType",
    "VerificationInfo",
    "DebuggingState",
    "RejectedHypothesis",
    "Action",
    "ActionType",
    "DebuggingStatus",
    "ContextPackage",
    "ContextSection",
    "DebuggingSession",
    "HypothesisRecord",
    "ActionRecord",
    "ContextPackageRecord",
    "SessionStatus",
]
