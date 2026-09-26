"""Unit tests for ContextSource implementations."""

import tempfile
from pathlib import Path

import pytest

from contextforge.ingestion import (
    FileSource,
    TextSource,
    TaskSource,
    ToolOutputSource,
    TestResultSource,
)
from contextforge.models import ContextType, ItemStatus


def test_file_source_basic():
    """Test FileSource ingests files correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "test.py").write_text("print('hello')")
        (root / "README.md").write_text("# Test Project")

        source = FileSource(root_path=root, patterns=["*.py", "*.md"], task_id="task-123")
        items = source.fetch()

        assert len(items) == 2
        types = {item.type for item in items}
        assert types == {ContextType.FILE}

        # Check provenance
        for item in items:
            assert item.provenance.source_type.value == "file"
            assert item.provenance.task_id == "task-123"
            assert item.provenance.observer == "file_ingestion"


def test_file_source_filters_by_pattern():
    """Test FileSource respects patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "test.py").write_text("print('hello')")
        (root / "config.json").write_text("{}")

        source = FileSource(root_path=root, patterns=["*.py"], task_id="task-123")
        items = source.fetch()

        assert len(items) == 1
        assert items[0].source == "test.py"


def test_text_source_basic():
    """Test TextSource creates log items."""
    source = TextSource(
        content="Error: Connection timeout",
        source_id="app.log",
        context_type=ContextType.LOG,
        task_id="task-123",
    )
    items = source.fetch()

    assert len(items) == 1
    assert items[0].type == ContextType.LOG
    assert items[0].content == "Error: Connection timeout"
    assert items[0].provenance.source_type.value == "tool"


def test_task_source_basic():
    """Test TaskSource creates task items."""
    source = TaskSource(
        task_description="Debug OAuth refresh 401",
        task_id="task-123",
        observer="developer",
    )
    items = source.fetch()

    assert len(items) == 1
    assert items[0].type == ContextType.TASK
    assert items[0].status == ItemStatus.VERIFIED
    assert items[0].importance == 1.0
    assert items[0].provenance.source_type.value == "user"
    assert items[0].provenance.task_id == "task-123"


def test_tool_output_source():
    """Test ToolOutputSource creates tool output items."""
    source = ToolOutputSource(
        tool_name="pytest",
        output="FAILED tests/test_auth.py::test_refresh - AssertionError",
        task_id="task-123",
    )
    items = source.fetch()

    assert len(items) == 1
    assert items[0].type == ContextType.TOOL_OUTPUT
    assert items[0].source == "pytest"
    assert items[0].provenance.source_type.value == "tool"


def test_test_result_source():
    """Test TestResultSource creates test result items."""
    source = TestResultSource(
        test_output="test_refresh FAILED",
        test_file="tests/test_auth.py",
        task_id="task-123",
    )
    items = source.fetch()

    assert len(items) == 1
    assert items[0].type == ContextType.TEST_RESULT
    assert items[0].source == "tests/test_auth.py"
    assert items[0].provenance.source_type.value == "tool"


def test_empty_sources_return_empty():
    """Test empty content returns empty list."""
    text_source = TextSource(content="", source_id="empty.log")
    assert text_source.fetch() == []

    tool_source = ToolOutputSource(tool_name="test", output="")
    assert tool_source.fetch() == []

    test_source = TestResultSource(test_output="", test_file="test.py")
    assert test_source.fetch() == []