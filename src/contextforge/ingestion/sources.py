"""ContextSource implementations for ingesting from various sources."""

from pathlib import Path

from contextforge.models import (
    ContextItem,
    ContextType,
    ItemStatus,
    Provenance,
    SourceType,
)


class FileSource:
    """Ingest context from source files."""

    def __init__(
        self,
        root_path: Path,
        patterns: list[str] | None = None,
        task_id: str | None = None,
        observer: str = "file_ingestion",
    ) -> None:
        self.root_path = Path(root_path)
        self.patterns = patterns or ["*.py", "*.md", "*.txt", "*.json", "*.yaml", "*.yml"]
        self.task_id = task_id
        self.observer = observer

    def fetch(self) -> list[ContextItem]:
        """Fetch context items from files matching patterns."""
        items = []
        for pattern in self.patterns:
            for file_path in self.root_path.rglob(pattern):
                if file_path.is_file():
                    try:
                        content = file_path.read_text(encoding="utf-8")
                        if content.strip():
                            rel_path = file_path.relative_to(self.root_path)
                            items.append(self._create_item(str(rel_path), content))
                    except (UnicodeDecodeError, OSError):
                        # Skip binary or unreadable files
                        continue
        return items

    def _create_item(self, rel_path: str, content: str) -> ContextItem:
        """Create a ContextItem from a file."""
        provenance = Provenance.from_file(
            file_path=rel_path,
            observer=self.observer,
            task_id=self.task_id,
        )
        return ContextItem(
            type=ContextType.FILE,
            content=content,
            source=rel_path,
            provenance=provenance,
            importance=0.5,
            freshness=1.0,
            status=ItemStatus.UNVERIFIED,
        )

    def name(self) -> str:
        return f"FileSource({self.root_path})"


class TextSource:
    """Ingest context from raw text/log content."""

    def __init__(
        self,
        content: str,
        source_id: str,
        context_type: ContextType = ContextType.LOG,
        task_id: str | None = None,
        observer: str = "text_ingestion",
        importance: float = 0.5,
    ) -> None:
        self.content = content
        self.source_id = source_id
        self.context_type = context_type
        self.task_id = task_id
        self.observer = observer
        self.importance = importance

    def fetch(self) -> list[ContextItem]:
        """Fetch context item from the text content."""
        if not self.content.strip():
            return []

        provenance = Provenance(
            source_type=SourceType.FILE if self.context_type == ContextType.FILE else SourceType.TOOL,
            source_id=self.source_id,
            observer=self.observer,
            task_id=self.task_id,
        )
        return [
            ContextItem(
                type=self.context_type,
                content=self.content,
                source=self.source_id,
                provenance=provenance,
                importance=self.importance,
                freshness=1.0,
                status=ItemStatus.UNVERIFIED,
            )
        ]

    def name(self) -> str:
        return f"TextSource({self.source_id})"


class TaskSource:
    """Ingest the developer's debugging task as context."""

    def __init__(
        self,
        task_description: str,
        task_id: str,
        observer: str = "developer",
        importance: float = 1.0,
    ) -> None:
        self.task_description = task_description
        self.task_id = task_id
        self.observer = observer
        self.importance = importance

    def fetch(self) -> list[ContextItem]:
        """Fetch the task as a context item."""
        provenance = Provenance.from_user(
            user_id=self.observer,
            task_id=self.task_id,
        )
        return [
            ContextItem(
                type=ContextType.TASK,
                content=self.task_description,
                source="developer_task",
                provenance=provenance,
                importance=self.importance,
                freshness=1.0,
                status=ItemStatus.VERIFIED,
            )
        ]

    def name(self) -> str:
        return f"TaskSource({self.task_id})"


class ToolOutputSource:
    """Ingest context from tool output (test results, linter output, etc.)."""

    def __init__(
        self,
        tool_name: str,
        output: str,
        task_id: str | None = None,
        observer: str = "tool_ingestion",
        importance: float = 0.7,
    ) -> None:
        self.tool_name = tool_name
        self.output = output
        self.task_id = task_id
        self.observer = observer
        self.importance = importance

    def fetch(self) -> list[ContextItem]:
        """Fetch context item from tool output."""
        if not self.output.strip():
            return []

        provenance = Provenance.from_tool(
            tool_name=self.tool_name,
            observer=self.observer,
            task_id=self.task_id,
        )
        return [
            ContextItem(
                type=ContextType.TOOL_OUTPUT,
                content=self.output,
                source=self.tool_name,
                provenance=provenance,
                importance=self.importance,
                freshness=1.0,
                status=ItemStatus.UNVERIFIED,
            )
        ]

    def name(self) -> str:
        return f"ToolOutputSource({self.tool_name})"


class TestResultSource:
    """Ingest context from test results."""

    def __init__(
        self,
        test_output: str,
        test_file: str,
        task_id: str | None = None,
        observer: str = "test_runner",
        importance: float = 0.8,
    ) -> None:
        self.test_output = test_output
        self.test_file = test_file
        self.task_id = task_id
        self.observer = observer
        self.importance = importance

    def fetch(self) -> list[ContextItem]:
        """Fetch context item from test results."""
        if not self.test_output.strip():
            return []

        provenance = Provenance.from_tool(
            tool_name=f"pytest:{self.test_file}",
            observer=self.observer,
            task_id=self.task_id,
        )
        return [
            ContextItem(
                type=ContextType.TEST_RESULT,
                content=self.test_output,
                source=self.test_file,
                provenance=provenance,
                importance=self.importance,
                freshness=1.0,
                status=ItemStatus.UNVERIFIED,
            )
        ]

    def name(self) -> str:
        return f"TestResultSource({self.test_file})"