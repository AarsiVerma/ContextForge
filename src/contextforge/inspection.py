"""Inspection and debug mode for the context pipeline."""

from dataclasses import dataclass, field
from typing import Any

from contextforge.models import ContextItem, ContextIR, ContextPackage
from contextforge.retrieval.selector import SelectionResult


@dataclass
class PipelineStage:
    """Represents a stage in the pipeline."""

    name: str
    input_count: int
    output_count: int
    metrics: dict[str, Any] = field(default_factory=dict)
    items: list[ContextItem] = field(default_factory=list)


class PipelineInspector:
    """Inspect and debug the context pipeline."""

    def __init__(self) -> None:
        self.stages: list[PipelineStage] = []

    def record_ingestion(self, items: list[ContextItem]) -> None:
        """Record the ingestion stage."""
        self.stages.append(
            PipelineStage(
                name="INGESTION",
                input_count=0,
                output_count=len(items),
                metrics={"total_items": len(items)},
                items=items,
            )
        )

    def record_normalization(self, raw_items: list[ContextItem], normalized_items: list[ContextItem]) -> None:
        """Record the normalization stage."""
        self.stages.append(
            PipelineStage(
                name="NORMALIZATION",
                input_count=len(raw_items),
                output_count=len(normalized_items),
                metrics={
                    "input_items": len(raw_items),
                    "output_items": len(normalized_items),
                },
                items=normalized_items,
            )
        )

    def record_retrieval(
        self,
        query: str | None,
        candidates: list[ContextItem],
        retrieved: list[ContextItem],
    ) -> None:
        """Record the retrieval stage."""
        self.stages.append(
            PipelineStage(
                name="RETRIEVAL",
                input_count=len(candidates),
                output_count=len(retrieved),
                metrics={
                    "query": query,
                    "candidate_count": len(candidates),
                    "retrieved_count": len(retrieved),
                },
                items=retrieved,
            )
        )

    def record_ranking(
        self,
        retrieved: list[ContextItem],
        ranked: list[ContextItem],
    ) -> None:
        """Record the ranking stage."""
        self.stages.append(
            PipelineStage(
                name="RANKING",
                input_count=len(retrieved),
                output_count=len(ranked),
                metrics={
                    "input_count": len(retrieved),
                    "output_count": len(ranked),
                },
                items=ranked,
            )
        )

    def record_selection(self, selection: SelectionResult) -> None:
        """Record the selection stage."""
        self.stages.append(
            PipelineStage(
                name="SELECTION",
                input_count=selection.metrics.get("candidate_items", 0),
                output_count=selection.metrics.get("selected_items", 0),
                metrics=selection.metrics,
                items=selection.selected,
            )
        )

    def record_compilation(self, package: ContextPackage, selection: SelectionResult | None = None) -> None:
        """Record the compilation stage."""
        metrics = {
            "sections": len(package.sections),
            "total_tokens": package.total_tokens,
        }
        if selection:
            metrics.update(selection.metrics)
        self.stages.append(
            PipelineStage(
                name="COMPILATION",
                input_count=selection.metrics.get("selected_items", 0) if selection else 0,
                output_count=1,
                metrics=metrics,
                items=[],
            )
        )

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of all pipeline stages."""
        return {
            "stages": [
                {
                    "name": s.name,
                    "input_count": s.input_count,
                    "output_count": s.output_count,
                    "metrics": s.metrics,
                }
                for s in self.stages
            ],
            "total_stages": len(self.stages),
        }

    def print_summary(self) -> None:
        """Print a human-readable summary."""
        print("\n" + "=" * 60)
        print("CONTEXTFORGE PIPELINE INSPECTION")
        print("=" * 60)

        for i, stage in enumerate(self.stages):
            print(f"\n[{i+1}] {stage.name}")
            print(f"    Input:  {stage.input_count} items")
            print(f"    Output: {stage.output_count} items")
            if stage.metrics:
                for key, value in stage.metrics.items():
                    print(f"    {key}: {value}")

        print("\n" + "=" * 60)

    def print_detailed(self, stage_name: str | None = None) -> None:
        """Print detailed item information for a stage."""
        stages_to_show = self.stages
        if stage_name:
            stages_to_show = [s for s in self.stages if s.name == stage_name.upper()]

        for stage in stages_to_show:
            print(f"\n{'=' * 60}")
            print(f"STAGE: {stage.name} ({stage.output_count} items)")
            print(f"{'=' * 60}")

            for i, item in enumerate(stage.items[:10]):  # Limit to first 10
                print(f"\n  [{i+1}] {item.type.value} | {item.status.value} | {item.source}")
                print(f"      Content: {item.content[:150]}...")
                print(f"      ID: {item.id[:8]}...")
                print(f"      Importance: {item.importance:.2f} | Freshness: {item.freshness:.2f}")
                print(f"      Provenance: {item.provenance.source_type.value}:{item.provenance.source_id}")

            if len(stage.items) > 10:
                print(f"\n  ... and {len(stage.items) - 10} more items")

    def clear(self) -> None:
        """Clear all recorded stages."""
        self.stages.clear()


class DebugContext:
    """Debug context for a single debugging task."""

    def __init__(self, task_id: str, task_description: str) -> None:
        self.task_id = task_id
        self.task_description = task_description
        self.inspector = PipelineInspector()
        self.raw_sources: list[Any] = []
        self.normalized_items: list[ContextItem] = []
        self.candidates: list[ContextItem] = []
        self.retrieved_items: list[ContextItem] = []
        self.ranked_items: list[ContextItem] = []
        self.selection_result: SelectionResult | None = None
        self.final_package: ContextPackage | None = None

    def to_dict(self) -> dict[str, Any]:
        """Export debug context as dictionary."""
        return {
            "task_id": self.task_id,
            "task_description": self.task_description,
            "pipeline": self.inspector.get_summary(),
            "raw_sources_count": len(self.raw_sources),
            "normalized_items_count": len(self.normalized_items),
            "candidates_count": len(self.candidates),
            "retrieved_count": len(self.retrieved_items),
            "ranked_count": len(self.ranked_items),
            "selection_metrics": self.selection_result.metrics if self.selection_result else None,
            "final_package_tokens": self.final_package.total_tokens if self.final_package else None,
        }