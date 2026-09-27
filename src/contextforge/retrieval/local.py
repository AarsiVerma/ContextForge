"""Deterministic local retrieval backend implementation."""


from contextforge.models import ContextIR, ContextItem
from contextforge.storage.base import ContextStore


class DeterministicRetriever:
    """Deterministic retriever using token overlap and metadata filtering."""

    def __init__(self, store: ContextStore) -> None:
        self.store = store

    def retrieve(
        self,
        task_id: str,
        query: str | None = None,
        types: list[str] | None = None,
        limit: int = 50,
    ) -> list[ContextItem]:
        """Retrieve items relevant to a task using deterministic matching."""
        # First, get all items for the task
        items = self.store.list_items(task_id=task_id, limit=limit * 2)

        # Apply type filter if provided
        if types:
            items = [item for item in items if item.type.value in types]

        # If no query, return all (up to limit)
        if not query:
            return items[:limit]

        # Score items by token overlap with query
        query_terms = set(query.lower().split())
        if not query_terms:
            return items[:limit]

        scored_items = []
        for item in items:
            score = self._compute_relevance_score(item, query_terms)
            if score > 0:
                scored_items.append((score, item))

        # Sort by score descending
        scored_items.sort(key=lambda x: -x[0])
        return [item for _, item in scored_items[:limit]]

    def retrieve_by_ir(self, ir: ContextIR, limit: int = 50) -> list[ContextItem]:
        """Retrieve items for a ContextIR."""
        return self.retrieve(task_id=ir.task_id, limit=limit)

    def _compute_relevance_score(self, item: ContextItem, query_terms: set[str]) -> float:
        """Compute token overlap relevance score."""
        content_terms = set(item.content.lower().split())
        source_terms = set(item.source.lower().split())
        tag_terms = {tag.lower() for tag in item.tags}

        all_item_terms = content_terms | source_terms | tag_terms

        if not all_item_terms:
            return 0.0

        overlap = len(query_terms & all_item_terms)
        return overlap / len(query_terms)


class LocalRetriever:
    """Local retriever using the store directly."""

    def __init__(self, store: ContextStore) -> None:
        self.store = store
        self._deterministic = DeterministicRetriever(store)

    def retrieve(
        self,
        task_id: str,
        query: str | None = None,
        types: list[str] | None = None,
        limit: int = 50,
    ) -> list[ContextItem]:
        """Retrieve items relevant to a task."""
        return self._deterministic.retrieve(task_id, query, types, limit)

    def retrieve_by_ir(self, ir: ContextIR, limit: int = 50) -> list[ContextItem]:
        """Retrieve items for a ContextIR."""
        return self._deterministic.retrieve_by_ir(ir, limit)