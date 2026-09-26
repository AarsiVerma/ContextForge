"""Unit tests for context compilation."""

from contextforge.compilation import SimpleCompiler
from contextforge.models import (
    ContextIR,
    ContextItem,
    ContextType,
    ItemStatus,
    Provenance,
    SourceType,
)
from contextforge.ranking import DeterministicRanker


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


def test_compiler_basic() -> None:
    """Test basic compilation."""
    ir = ContextIR(task_id="task-123", task_description="Debug login")
    ir.add_item(make_item(ContextType.TASK, "Debug login issue"))
    ir.add_item(make_item(ContextType.EVIDENCE, "Token expires in 1 hour"))
    ir.add_item(make_item(ContextType.FILE, "auth.py", source="auth.py"))

    ranker = DeterministicRanker()
    ranked = ranker.rank(ir.items, "task-123")

    compiler = SimpleCompiler()
    package = compiler.compile(ir, ranked)

    assert package.task_id == "task-123"
    assert package.task_description == "Debug login"
    assert len(package.sections) > 0
    assert package.total_tokens > 0


def test_compiler_sections() -> None:
    """Test that expected sections are created."""
    ir = ContextIR(task_id="task-123", task_description="Test")
    ir.add_item(make_item(ContextType.TASK, "Task details"))
    ir.add_item(make_item(ContextType.EVIDENCE, "Evidence 1"))
    ir.add_item(make_item(ContextType.EVIDENCE, "Evidence 2", status=ItemStatus.VERIFIED))
    ir.add_item(make_item(ContextType.FILE, "auth.py", source="auth.py"))
    ir.add_item(make_item(ContextType.HYPOTHESIS, "Token issue"))
    ir.add_item(make_item(ContextType.EVIDENCE, "Rejected", status=ItemStatus.REJECTED))
    ir.add_item(make_item(ContextType.PROJECT_STATE, "Python 3.12"))

    ranker = DeterministicRanker()
    ranked = ranker.rank(ir.items, "task-123")

    compiler = SimpleCompiler()
    package = compiler.compile(ir, ranked)

    section_titles = [s.title for s in package.sections]
    assert "TASK" in section_titles
    assert "VERIFIED EVIDENCE" in section_titles
    assert "RELEVANT FILES" in section_titles
    assert "CURRENT HYPOTHESIS" in section_titles
    assert "REJECTED HYPOTHESES" in section_titles
    assert "PROJECT STATE" in section_titles
    assert "PROVENANCE" in section_titles


def test_compiler_token_budget() -> None:
    """Test compiler respects token budget."""
    ir = ContextIR(task_id="task-123", task_description="Test")
    # Add many items
    for i in range(20):
        ir.add_item(make_item(ContextType.EVIDENCE, f"Evidence {i}" * 50))

    ranker = DeterministicRanker()
    ranked = ranker.rank(ir.items, "task-123")

    compiler = SimpleCompiler()
    package = compiler.compile(ir, ranked)

    assert package.total_tokens <= compiler.config.max_context_tokens


def test_compiler_markdown_output() -> None:
    """Test markdown output format."""
    ir = ContextIR(task_id="task-123", task_description="Debug login")
    ir.add_item(make_item(ContextType.TASK, "Debug login issue"))
    ir.add_item(
        make_item(ContextType.EVIDENCE, "Token expires in 1 hour", status=ItemStatus.VERIFIED)
    )

    ranker = DeterministicRanker()
    ranked = ranker.rank(ir.items, "task-123")

    compiler = SimpleCompiler()
    package = compiler.compile(ir, ranked)

    md = package.to_markdown()
    assert "# Context Package: Debug login" in md
    assert "## TASK" in md
    assert "## VERIFIED EVIDENCE" in md
    assert "Token expires in 1 hour" in md


def test_compiler_json_output() -> None:
    """Test JSON output format."""
    ir = ContextIR(task_id="task-123", task_description="Test")
    ir.add_item(make_item(ContextType.TASK, "Task"))

    ranker = DeterministicRanker()
    ranked = ranker.rank(ir.items, "task-123")

    compiler = SimpleCompiler()
    package = compiler.compile(ir, ranked)

    json_str = package.to_json()
    assert "task-123" in json_str
    assert "Debug login" in json_str or "Test" in json_str


def test_compiler_provenance_summary() -> None:
    """Test provenance summary in package."""
    ir = ContextIR(task_id="task-123", task_description="Test")
    ir.add_item(make_item(ContextType.EVIDENCE, "From file", source_type=SourceType.FILE))
    ir.add_item(make_item(ContextType.EVIDENCE, "From tool", source_type=SourceType.TOOL))
    ir.add_item(make_item(ContextType.EVIDENCE, "From file 2", source_type=SourceType.FILE))

    ranker = DeterministicRanker()
    ranked = ranker.rank(ir.items, "task-123")

    compiler = SimpleCompiler()
    package = compiler.compile(ir, ranked)

    assert "total_items" in package.provenance_summary
    assert "by_source_type" in package.provenance_summary
    assert "by_status" in package.provenance_summary
    assert "unique_sources" in package.provenance_summary
    assert package.provenance_summary["by_source_type"]["file"] == 2
    assert package.provenance_summary["by_source_type"]["tool"] == 1


def test_compiler_empty_items() -> None:
    """Test compilation with no items."""
    ir = ContextIR(task_id="task-123", task_description="Empty test")

    ranker = DeterministicRanker()
    ranked = ranker.rank([], "task-123")

    compiler = SimpleCompiler()
    package = compiler.compile(ir, ranked)

    # TASK section is always created
    assert package.total_tokens > 0
    assert len(package.sections) == 1
    assert package.sections[0].title == "TASK"
