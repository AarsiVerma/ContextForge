"""Ranking interface - ContextRanker protocol and deterministic implementation."""

from typing import Protocol

from contextforge.config import get_config
from contextforge.models import ContextItem


class ContextRanker(Protocol):
    """Protocol for ranking context items by relevance."""

    def rank(
        self,
        items: list[ContextItem],
        task_id: str,
        query: str | None = None,
    ) -> list[ContextItem]:
        """Rank items by relevance to task/query. Returns sorted list (highest first)."""
        ...


class DeterministicRanker:
    """Deterministic baseline ranker using multiple signals.

    Signals (weighted):
    - relevance: keyword overlap with task/query (0.30)
    - freshness: temporal recency (0.20)
    - importance: explicit importance score (0.20)
    - verification: verified > unverified > rejected (0.15)
    - source_reliability: file/tool > agent > user > inference (0.10)
    - task_relationship: same task_id (0.05)
    """

    def __init__(self) -> None:
        self.config = get_config()
        self._source_weights = {
            "file": 1.0,
            "tool": 0.9,
            "user": 0.7,
            "agent": 0.6,
            "inference": 0.5,
        }
        self._status_weights = {
            "verified": 1.0,
            "unverified": 0.5,
            "rejected": 0.1,
            "superseded": 0.2,
        }

    def rank(
        self,
        items: list[ContextItem],
        task_id: str,
        query: str | None = None,
    ) -> list[ContextItem]:
        """Rank items deterministically."""
        scored = []
        for item in items:
            score = self._score_item(item, task_id, query)
            scored.append((score, item))

        # Sort by score descending, then by updated_at descending for tie-breaking
        scored.sort(key=lambda x: (-x[0], -x[1].updated_at.timestamp()))
        return [item for _, item in scored]

    def _score_item(
        self,
        item: ContextItem,
        task_id: str,
        query: str | None,
    ) -> float:
        """Calculate composite score for an item."""
        # Relevance: keyword overlap
        relevance = self._compute_relevance(item, query)

        # Freshness: already normalized 0-1
        freshness = item.freshness

        # Importance: already normalized 0-1
        importance = item.importance

        # Verification status
        verification = self._status_weights.get(item.status.value, 0.5)

        # Source reliability
        source_rel = self._source_weights.get(item.provenance.source_type.value, 0.5)

        # Task relationship
        task_rel = 1.0 if item.provenance.task_id == task_id else 0.0

        # Weighted composite
        score = (
            0.30 * relevance
            + 0.20 * freshness
            + 0.20 * importance
            + 0.15 * verification
            + 0.10 * source_rel
            + 0.05 * task_rel
        )

        return score

    def _compute_relevance(self, item: ContextItem, query: str | None) -> float:
        """Compute keyword-based relevance score."""
        if not query:
            return 0.5

        query_terms = set(query.lower().split())
        content_terms = set(item.content.lower().split())
        source_terms = set(item.source.lower().split())
        tag_terms = {tag.lower() for tag in item.tags}

        all_item_terms = content_terms | source_terms | tag_terms

        if not query_terms or not all_item_terms:
            return 0.0

        overlap = len(query_terms & all_item_terms)
        return min(1.0, overlap / len(query_terms))
