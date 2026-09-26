"""Context selection with budget enforcement and duplicate removal."""

from dataclasses import dataclass
from typing import Any

from contextforge.models import ContextItem
from contextforge.config import get_config


@dataclass
class SelectionResult:
    """Result of context selection."""

    selected: list[ContextItem]
    discarded: list[ContextItem]
    duplicates_removed: list[ContextItem]
    metrics: dict[str, Any]


class ContextSelector:
    """Select context items under token budget with priority preservation."""

    def __init__(self, max_tokens: int | None = None) -> None:
        self.config = get_config()
        self.max_tokens = max_tokens or self.config.max_context_tokens

    def select(
        self,
        items: list[ContextItem],
        task_id: str,
        query: str | None = None,
    ) -> SelectionResult:
        """Select items under token budget."""
        # Remove duplicates first
        unique_items, duplicates = self._deduplicate(items)

        # Score items for selection priority
        scored_items = self._score_for_selection(unique_items, task_id, query)

        # Select under budget
        selected = []
        discarded = []
        used_tokens = 0

        for score, item, tokens in scored_items:
            if used_tokens + tokens <= self.max_tokens:
                selected.append(item)
                used_tokens += tokens
            else:
                discarded.append(item)

        # Build metrics
        metrics = {
            "candidate_items": len(items),
            "unique_items": len(unique_items),
            "duplicates_removed": len(duplicates),
            "selected_items": len(selected),
            "discarded_items": len(discarded),
            "estimated_tokens": used_tokens,
            "budget": self.max_tokens,
            "compression_ratio": len(selected) / len(items) if items else 0.0,
            "token_utilization": used_tokens / self.max_tokens if self.max_tokens > 0 else 0.0,
        }

        return SelectionResult(
            selected=selected,
            discarded=discarded,
            duplicates_removed=duplicates,
            metrics=metrics,
        )

    def _deduplicate(self, items: list[ContextItem]) -> tuple[list[ContextItem], list[ContextItem]]:
        """Remove duplicate items based on source + content."""
        seen: dict[tuple[str, str], ContextItem] = {}
        unique = []
        duplicates = []

        for item in items:
            key = (item.source, item.content[:200])  # First 200 chars for content
            if key not in seen:
                seen[key] = item
                unique.append(item)
            else:
                duplicates.append(item)

        return unique, duplicates

    def _score_for_selection(
        self, items: list[ContextItem], task_id: str, query: str | None
    ) -> list[tuple[float, ContextItem, int]]:
        """Score items for selection priority."""
        from contextforge.ranking import DeterministicRanker

        ranker = DeterministicRanker()
        ranked = ranker.rank(items, task_id, query)

        scored = []
        for item in ranked:
            tokens = self._estimate_tokens(item.content)
            # Priority factors
            priority = 0.0

            # Verified items get higher priority
            if item.status.value == "verified":
                priority += 10.0

            # High importance
            priority += item.importance * 5.0

            # Fresh items
            priority += item.freshness * 3.0

            # Task-specific items
            if item.provenance.task_id == task_id:
                priority += 2.0

            # Evidence and facts are more important than hypotheses
            if item.type.value in ("evidence", "fact", "test_result"):
                priority += 3.0
            elif item.type.value == "file":
                priority += 2.0

            scored.append((priority, item, tokens))

        # Sort by priority descending
        scored.sort(key=lambda x: -x[0])
        return scored

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate: ~4 chars per token."""
        return max(1, len(text) // 4)