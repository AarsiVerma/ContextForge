"""ContextForge - Model-agnostic context management for AI coding agents."""

from contextforge.compilation import ContextCompiler, SimpleCompiler, CompilationMetrics
from contextforge.ingestion import (
    ContextSource,
    FileSource,
    TextSource,
    TaskSource,
    ToolOutputSource,
    TestResultSource,
    Normalizer,
    normalize_sources,
)
from contextforge.models import (
    Action,
    ActionType,
    ContextIR,
    ContextItem,
    ContextPackage,
    ContextSection,
    ContextType,
    DebuggingSession,
    DebuggingState,
    DebuggingStatus,
    HypothesisRecord,
    ActionRecord,
    ContextPackageRecord,
    SessionStatus,
    ItemStatus,
    Provenance,
    RejectedHypothesis,
    SourceType,
    VerificationInfo,
)
from contextforge.ranking import ContextRanker, DeterministicRanker
from contextforge.retrieval import (
    ContextRetriever,
    LocalRetriever,
    DeterministicRetriever,
    ContextSelector,
    SelectionResult,
)
from contextforge.storage import ContextStore, SQLiteStore

__version__ = "0.1.0"

__all__ = [
    # Models
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
    # Storage
    "ContextStore",
    "SQLiteStore",
    # Ingestion
    "ContextSource",
    "FileSource",
    "TextSource",
    "TaskSource",
    "ToolOutputSource",
    "TestResultSource",
    "Normalizer",
    "normalize_sources",
    # Retrieval
    "ContextRetriever",
    "LocalRetriever",
    "DeterministicRetriever",
    "ContextSelector",
    "SelectionResult",
    # Ranking
    "ContextRanker",
    "DeterministicRanker",
    # Compilation
    "ContextCompiler",
    "SimpleCompiler",
    "CompilationMetrics",
]
