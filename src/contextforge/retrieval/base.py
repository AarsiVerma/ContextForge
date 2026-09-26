"""Retrieval interface - ContextRetriever protocol."""

from typing import Protocol

from contextforge.models import ContextIR, ContextItem


class ContextRetriever(Protocol):
    """Protocol for retrieving relevant context items."""

    def retrieve(
        self,
        task_id: str,
        query: str | None = None,
        types: list[str] | None = None,
        limit: int = 50,
    ) -> list[ContextItem]:
        """Retrieve items relevant to a task."""
        ...

    def retrieve_by_ir(self, ir: ContextIR, limit: int = 50) -> list[ContextItem]:
        """Retrieve items for a ContextIR."""
        ...
