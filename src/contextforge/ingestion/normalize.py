"""Normalization layer for converting raw sources to ContextItems."""

from pathlib import Path
from typing import Any

from contextforge.models import (
    ContextItem,
    ContextType,
    ItemStatus,
    Provenance,
    SourceType,
)


class Normalizer:
    """Normalize raw context into structured ContextItems."""

    def __init__(self, task_id: str | None = None, observer: str = "normalizer") -> None:
        self.task_id = task_id
        self.observer = observer

    def normalize_file(self, file_path: Path, content: str, rel_path: str | None = None) -> ContextItem:
        """Normalize a source file into a ContextItem."""
        source = rel_path or str(file_path)
        provenance = Provenance.from_file(
            file_path=source,
            observer=self.observer,
            task_id=self.task_id,
        )
        return ContextItem(
            type=ContextType.FILE,
            content=content,
            source=source,
            provenance=provenance,
            importance=self._infer_importance_file(file_path),
            freshness=1.0,
            status=ItemStatus.UNVERIFIED,
        )

    def normalize_log(self, content: str, source_id: str, importance: float = 0.6) -> ContextItem:
        """Normalize log content into a ContextItem."""
        provenance = Provenance(
            source_type=SourceType.TOOL,
            source_id=source_id,
            observer=self.observer,
            task_id=self.task_id,
        )
        return ContextItem(
            type=ContextType.LOG,
            content=content,
            source=source_id,
            provenance=provenance,
            importance=importance,
            freshness=1.0,
            status=ItemStatus.UNVERIFIED,
        )

    def normalize_test_result(
        self, content: str, test_file: str, importance: float = 0.8
    ) -> ContextItem:
        """Normalize test result into a ContextItem."""
        provenance = Provenance.from_tool(
            tool_name=f"pytest:{test_file}",
            observer=self.observer,
            task_id=self.task_id,
        )
        return ContextItem(
            type=ContextType.TEST_RESULT,
            content=content,
            source=test_file,
            provenance=provenance,
            importance=importance,
            freshness=1.0,
            status=ItemStatus.UNVERIFIED,
        )

    def normalize_tool_output(
        self, content: str, tool_name: str, importance: float = 0.7
    ) -> ContextItem:
        """Normalize tool output into a ContextItem."""
        provenance = Provenance.from_tool(
            tool_name=tool_name,
            observer=self.observer,
            task_id=self.task_id,
        )
        return ContextItem(
            type=ContextType.TOOL_OUTPUT,
            content=content,
            source=tool_name,
            provenance=provenance,
            importance=importance,
            freshness=1.0,
            status=ItemStatus.UNVERIFIED,
        )

    def normalize_fact(
        self, content: str, source: str, evidence_ids: list[str] | None = None
    ) -> ContextItem:
        """Normalize a verified fact into a ContextItem."""
        provenance = Provenance(
            source_type=SourceType.INFERENCE,
            source_id=source,
            observer=self.observer,
            task_id=self.task_id,
        )
        item = ContextItem(
            type=ContextType.FACT,
            content=content,
            source=source,
            provenance=provenance,
            importance=0.9,
            freshness=1.0,
            status=ItemStatus.VERIFIED,
        )
        if evidence_ids:
            from contextforge.models.provenance import VerificationInfo
            item.provenance.verification = VerificationInfo(
                method="normalized_from_evidence",
                verified_by="normalizer",
                evidence_ids=evidence_ids,
            )
        return item

    def normalize_constraint(self, content: str, source: str) -> ContextItem:
        """Normalize a constraint into a ContextItem."""
        provenance = Provenance(
            source_type=SourceType.INFERENCE,
            source_id=source,
            observer=self.observer,
            task_id=self.task_id,
        )
        return ContextItem(
            type=ContextType.CONSTRAINT,
            content=content,
            source=source,
            provenance=provenance,
            importance=0.8,
            freshness=1.0,
            status=ItemStatus.VERIFIED,
        )

    def _infer_importance_file(self, file_path: Path) -> float:
        """Infer importance based on file path patterns."""
        path_str = str(file_path).lower().replace("\\", "/")
        # Test files are highly relevant for debugging
        if "test" in path_str:
            return 0.8
        # Config files often contain important settings
        if any(name in path_str for name in ["config", "settings", "env"]):
            return 0.7
        # Source files in main directories
        if path_str.startswith("src/") or path_str.startswith("lib/"):
            return 0.6
        # Documentation
        if path_str.endswith((".md", ".rst", ".txt")):
            return 0.4
        return 0.5


def normalize_sources(sources: list[Any], task_id: str | None = None) -> list[ContextItem]:
    """Normalize a list of ContextSource objects into ContextItems."""
    items = []
    for source in sources:
        if hasattr(source, "fetch"):
            items.extend(source.fetch())
        else:
            # Assume it's already a ContextItem or compatible
            pass
    return items