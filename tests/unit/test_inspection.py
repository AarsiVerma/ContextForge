"""Unit tests for inspection/debug mode."""

import pytest

from contextforge.models import (
    ContextItem,
    ContextType,
    ItemStatus,
    ContextIR,
    Provenance,
    SourceType,
)
from contextforge.inspection import PipelineInspector, DebugContext
from contextforge.retrieval.selector import SelectionResult


def make_item(
    type_: ContextType,
    content: str,
    source: str = "test.py",
    source_type: SourceType = SourceType.FILE,
    importance: float = 0.5,
    status: ItemStatus = ItemStatus.UNVERIFIED,
    task_id: str = "task-123",
) -> ContextItem:
    """Helper to create a test item."""
    prov = Provenance(
        source_type=source_type,
        source_id=source,
        observer="test",
        task_id=task_id,
    )
    return ContextItem(
        type=type_,
        content=content,
        source=source,
        importance=importance,
        freshness=1.0,
        status=status,
        provenance=prov,
    )


def test_pipeline_inspector_stages():
    """Test inspector records stages."""
    inspector = PipelineInspector()

    items = [make_item(ContextType.EVIDENCE, f"Item {i}") for i in range(5)]
    inspector.record_ingestion(items)

    assert len(inspector.stages) == 1
    assert inspector.stages[0].name == "INGESTION"
    assert inspector.stages[0].output_count == 5


def test_pipeline_inspector_normalization():
    """Test normalization stage recording."""
    inspector = PipelineInspector()

    raw = [make_item(ContextType.EVIDENCE, "Raw")]
    normalized = [make_item(ContextType.EVIDENCE, "Normalized")]

    inspector.record_normalization(raw, normalized)

    assert len(inspector.stages) == 1
    assert inspector.stages[0].name == "NORMALIZATION"
    assert inspector.stages[0].input_count == 1
    assert inspector.stages[0].output_count == 1


def test_pipeline_inspector_retrieval():
    """Test retrieval stage recording."""
    inspector = PipelineInspector()

    candidates = [make_item(ContextType.EVIDENCE, f"Candidate {i}") for i in range(10)]
    retrieved = [make_item(ContextType.EVIDENCE, f"Retrieved {i}") for i in range(3)]

    inspector.record_retrieval("JWT token", candidates, retrieved)

    assert len(inspector.stages) == 1
    assert inspector.stages[0].name == "RETRIEVAL"
    assert inspector.stages[0].metrics["query"] == "JWT token"
    assert inspector.stages[0].metrics["candidate_count"] == 10
    assert inspector.stages[0].metrics["retrieved_count"] == 3


def test_pipeline_inspector_ranking():
    """Test ranking stage recording."""
    inspector = PipelineInspector()

    retrieved = [make_item(ContextType.EVIDENCE, f"Item {i}") for i in range(3)]
    ranked = list(reversed(retrieved))

    inspector.record_ranking(retrieved, ranked)

    assert len(inspector.stages) == 1
    assert inspector.stages[0].name == "RANKING"


def test_pipeline_inspector_selection():
    """Test selection stage recording."""
    inspector = PipelineInspector()

    selection = SelectionResult(
        selected=[make_item(ContextType.EVIDENCE, "Selected")],
        discarded=[make_item(ContextType.EVIDENCE, "Discarded")],
        duplicates_removed=[make_item(ContextType.EVIDENCE, "Duplicate")],
        metrics={
            "candidate_items": 10,
            "selected_items": 1,
            "discarded_items": 8,
            "duplicates_removed": 1,
            "estimated_tokens": 500,
            "budget": 8000,
            "compression_ratio": 0.1,
            "token_utilization": 0.0625,
        },
    )

    inspector.record_selection(selection)

    assert len(inspector.stages) == 1
    assert inspector.stages[0].name == "SELECTION"
    assert inspector.stages[0].metrics["candidate_items"] == 10


def test_pipeline_inspector_compilation():
    """Test compilation stage recording."""
    from contextforge.models import ContextPackage, ContextSection
    inspector = PipelineInspector()

    package = ContextPackage(
        task_id="task-123",
        task_description="Test",
        sections=[
            ContextSection(title="TASK", content="Task", priority=100, item_ids=[], token_estimate=10),
        ],
        total_tokens=500,
    )

    selection = SelectionResult(
        selected=[],
        discarded=[],
        duplicates_removed=[],
        metrics={"selected_items": 5},
    )

    inspector.record_compilation(package, selection)

    assert len(inspector.stages) == 1
    assert inspector.stages[0].name == "COMPILATION"
    assert inspector.stages[0].metrics["sections"] == 1
    assert inspector.stages[0].metrics["total_tokens"] == 500


def test_pipeline_inspector_summary():
    """Test summary generation."""
    inspector = PipelineInspector()

    items = [make_item(ContextType.EVIDENCE, f"Item {i}") for i in range(5)]
    inspector.record_ingestion(items)
    inspector.record_retrieval("query", items, items[:2])

    summary = inspector.get_summary()

    assert summary["total_stages"] == 2
    assert len(summary["stages"]) == 2
    assert summary["stages"][0]["name"] == "INGESTION"
    assert summary["stages"][1]["name"] == "RETRIEVAL"


def test_pipeline_inspector_clear():
    """Test clearing inspector."""
    inspector = PipelineInspector()

    items = [make_item(ContextType.EVIDENCE, "Item")]
    inspector.record_ingestion(items)
    inspector.clear()

    assert len(inspector.stages) == 0


def test_debug_context():
    """Test DebugContext tracks pipeline."""
    debug_ctx = DebugContext("task-123", "Debug OAuth")

    assert debug_ctx.task_id == "task-123"
    assert debug_ctx.task_description == "Debug OAuth"

    items = [make_item(ContextType.EVIDENCE, "Item")]
    debug_ctx.normalized_items = items
    debug_ctx.inspector.record_ingestion(items)

    d = debug_ctx.to_dict()

    assert d["task_id"] == "task-123"
    assert d["normalized_items_count"] == 1
    assert d["pipeline"]["total_stages"] == 1