"""Unit tests for enhanced compiler."""

import pytest

from contextforge.models import (
    ContextItem,
    ContextType,
    ItemStatus,
    ContextIR,
    Provenance,
    SourceType,
)
from contextforge.compilation import SimpleCompiler
from contextforge.ranking import DeterministicRanker
from contextforge.retrieval.selector import SelectionResult


def make_item(
    type_: ContextType,
    content: str,
    source: str = "test.py",
    source_type: SourceType = SourceType.FILE,
    importance: float = 0.5,
    freshness: float = 1.0,
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
        freshness=freshness,
        status=status,
        provenance=prov,
    )


def test_compiler_new_sections():
    """Test compiler includes new sections."""
    ir = ContextIR(task_id="task-123", task_description="Debug OAuth")
    ir.add_item(make_item(ContextType.TASK, "Debug OAuth refresh 401"))
    ir.add_item(make_item(ContextType.EVIDENCE, "Token expires in 30 min", status=ItemStatus.VERIFIED))
    ir.add_item(make_item(ContextType.TEST_RESULT, "test_refresh FAILED", source="tests/test_auth.py"))
    ir.add_item(make_item(ContextType.FILE, "auth.py content", source="auth.py"))
    ir.add_item(make_item(ContextType.LOG, "Error: Invalid token", source="app.log"))
    ir.add_item(make_item(ContextType.TOOL_OUTPUT, "pytest output", source="pytest"))
    ir.add_item(make_item(ContextType.HYPOTHESIS, "Race condition"))
    ir.add_item(make_item(ContextType.EVIDENCE, "Rejected", status=ItemStatus.REJECTED))
    ir.add_item(make_item(ContextType.CONSTRAINT, "Must rotate tokens"))

    ranker = DeterministicRanker()
    ranked = ranker.rank(ir.items, "task-123")

    compiler = SimpleCompiler()
    package = compiler.compile(ir, ranked)

    section_titles = [s.title for s in package.sections]
    assert "TASK" in section_titles
    assert "VERIFIED EVIDENCE" in section_titles
    assert "TEST RESULTS" in section_titles
    assert "RELEVANT FILES" in section_titles
    assert "LOGS" in section_titles
    assert "TOOL OUTPUT" in section_titles
    assert "CURRENT HYPOTHESIS" in section_titles
    assert "REJECTED HYPOTHESES" in section_titles
    assert "CONSTRAINTS" in section_titles
    assert "PROVENANCE" in section_titles


def test_compiler_provenance_summary_by_type():
    """Test provenance summary includes by_type."""
    ir = ContextIR(task_id="task-123", task_description="Test")
    ir.add_item(make_item(ContextType.EVIDENCE, "Evidence"))
    ir.add_item(make_item(ContextType.FILE, "File", source="file.py"))
    ir.add_item(make_item(ContextType.LOG, "Log", source="app.log"))

    ranker = DeterministicRanker()
    ranked = ranker.rank(ir.items, "task-123")

    compiler = SimpleCompiler()
    package = compiler.compile(ir, ranked)

    assert "by_type" in package.provenance_summary
    assert "evidence" in package.provenance_summary["by_type"]
    assert "file" in package.provenance_summary["by_type"]
    assert "log" in package.provenance_summary["by_type"]


def test_compile_with_selection():
    """Test compile_with_selection includes selection metrics."""
    ir = ContextIR(task_id="task-123", task_description="Test")
    ir.add_item(make_item(ContextType.TASK, "Task"))
    ir.add_item(make_item(ContextType.EVIDENCE, "Evidence", status=ItemStatus.VERIFIED))

    ranker = DeterministicRanker()
    ranked = ranker.rank(ir.items, "task-123")

    selection = SelectionResult(
        selected=ranked,
        discarded=[],
        duplicates_removed=[],
        metrics={
            "candidate_items": 10,
            "selected_items": 2,
            "discarded_items": 6,
            "duplicates_removed": 2,
            "estimated_tokens": 500,
            "budget": 8000,
            "compression_ratio": 0.2,
            "token_utilization": 0.0625,
        },
    )

    compiler = SimpleCompiler()
    package = compiler.compile_with_selection(ir, ranked, selection)

    assert "selection_metrics" in package.provenance_summary
    assert package.provenance_summary["selection_metrics"]["candidate_items"] == 10
    assert package.provenance_summary["selection_metrics"]["compression_ratio"] == 0.2


def test_compiler_token_budget():
    """Test compiler respects token budget."""
    ir = ContextIR(task_id="task-123", task_description="Test")
    # Add many items with content
    for i in range(20):
        ir.add_item(make_item(ContextType.EVIDENCE, f"Evidence {i}" * 100))

    ranker = DeterministicRanker()
    ranked = ranker.rank(ir.items, "task-123")

    compiler = SimpleCompiler()
    package = compiler.compile(ir, ranked)

    assert package.total_tokens <= compiler.config.max_context_tokens


def test_compiler_markdown_output():
    """Test markdown output format."""
    ir = ContextIR(task_id="task-123", task_description="Debug OAuth")
    ir.add_item(make_item(ContextType.TASK, "Debug OAuth refresh"))
    ir.add_item(make_item(ContextType.EVIDENCE, "Token expires", status=ItemStatus.VERIFIED))

    ranker = DeterministicRanker()
    ranked = ranker.rank(ir.items, "task-123")

    compiler = SimpleCompiler()
    package = compiler.compile(ir, ranked)

    md = package.to_markdown()
    assert "# Context Package: Debug OAuth" in md
    assert "## TASK" in md
    assert "## VERIFIED EVIDENCE" in md
    assert "Token expires" in md