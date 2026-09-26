"""Unit tests for normalization layer."""

import tempfile
from pathlib import Path

import pytest

from contextforge.ingestion import Normalizer, normalize_sources, FileSource
from contextforge.models import ContextType, ItemStatus, ContextItem


def test_normalize_file():
    """Test file normalization."""
    normalizer = Normalizer(task_id="task-123")
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.py"
        file_path.write_text("print('hello')")

        item = normalizer.normalize_file(file_path, "print('hello')", "test.py")

        assert item.type == ContextType.FILE
        assert item.content == "print('hello')"
        assert item.source == "test.py"
        assert item.provenance.task_id == "task-123"
        assert item.provenance.source_type.value == "file"


def test_normalize_log():
    """Test log normalization."""
    normalizer = Normalizer(task_id="task-123")
    item = normalizer.normalize_log("Error: Connection timeout", "app.log", importance=0.8)

    assert item.type == ContextType.LOG
    assert item.content == "Error: Connection timeout"
    assert item.source == "app.log"
    assert item.importance == 0.8


def test_normalize_test_result():
    """Test test result normalization."""
    normalizer = Normalizer(task_id="task-123")
    item = normalizer.normalize_test_result("test_refresh FAILED", "tests/test_auth.py")

    assert item.type == ContextType.TEST_RESULT
    assert item.content == "test_refresh FAILED"
    assert item.source == "tests/test_auth.py"
    assert item.importance == 0.8


def test_normalize_tool_output():
    """Test tool output normalization."""
    normalizer = Normalizer(task_id="task-123")
    item = normalizer.normalize_tool_output("Lint passed", "ruff")

    assert item.type == ContextType.TOOL_OUTPUT
    assert item.content == "Lint passed"
    assert item.source == "ruff"
    assert item.importance == 0.7


def test_normalize_fact():
    """Test fact normalization."""
    normalizer = Normalizer(task_id="task-123")
    item = normalizer.normalize_fact("JWT tokens expire in 30 minutes", "token.py", ["ev-1", "ev-2"])

    assert item.type == ContextType.FACT
    assert item.status == ItemStatus.VERIFIED
    assert item.importance == 0.9
    assert item.provenance.verification.evidence_ids == ["ev-1", "ev-2"]


def test_normalize_constraint():
    """Test constraint normalization."""
    normalizer = Normalizer(task_id="task-123")
    item = normalizer.normalize_constraint("Refresh tokens must rotate", "auth.md")

    assert item.type == ContextType.CONSTRAINT
    assert item.status == ItemStatus.VERIFIED
    assert item.importance == 0.8


def test_normalize_sources():
    """Test normalizing multiple sources."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "main.py").write_text("print('hello')")

        sources = [
            FileSource(root_path=root, patterns=["*.py"], task_id="task-123"),
        ]

        items = normalize_sources(sources, task_id="task-123")

        assert len(items) == 1
        assert items[0].type == ContextType.FILE


def test_infer_importance_file():
    """Test importance inference for different file types."""
    normalizer = Normalizer()

    assert normalizer._infer_importance_file(Path("tests/test_auth.py")) == 0.8
    assert normalizer._infer_importance_file(Path("src/config/settings.py")) == 0.7
    assert normalizer._infer_importance_file(Path("src/auth/token.py")) == 0.6
    assert normalizer._infer_importance_file(Path("README.md")) == 0.4
    assert normalizer._infer_importance_file(Path("random.txt")) == 0.4  # .txt matches documentation pattern