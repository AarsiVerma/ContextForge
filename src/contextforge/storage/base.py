"""Storage abstraction - ContextStore protocol."""

from __future__ import annotations

from typing import Protocol

from contextforge.models import ContextIR, ContextItem, DebuggingState


class ContextStore(Protocol):
    """Protocol for context storage backends."""

    def initialize(self) -> None:
        """Initialize the store (create tables, etc.)."""
        ...

    def close(self) -> None:
        """Close the store."""
        ...

    # ContextItem operations
    def put_item(self, item: ContextItem) -> None:
        """Store a context item."""
        ...

    def get_item(self, item_id: str) -> ContextItem | None:
        """Retrieve a context item by ID."""
        ...

    def delete_item(self, item_id: str) -> bool:
        """Delete a context item. Returns True if deleted."""
        ...

    def list_items(
        self,
        type_: str | None = None,
        status: str | None = None,
        task_id: str | None = None,
        tags: list[str] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ContextItem]:
        """List items with optional filters."""
        ...

    # ContextIR operations
    def put_ir(self, ir: ContextIR) -> None:
        """Store a ContextIR."""
        ...

    def get_ir(self, ir_id: str) -> ContextIR | None:
        """Retrieve a ContextIR by ID."""
        ...

    def get_ir_by_task(self, task_id: str) -> ContextIR | None:
        """Retrieve ContextIR by task ID."""
        ...

    def delete_ir(self, ir_id: str) -> bool:
        """Delete a ContextIR. Returns True if deleted."""
        ...

    # DebuggingState operations
    def put_state(self, state: DebuggingState) -> None:
        """Store debugging state."""
        ...

    def get_state(self, task_id: str) -> DebuggingState | None:
        """Retrieve debugging state by task ID."""
        ...

    def delete_state(self, task_id: str) -> bool:
        """Delete debugging state. Returns True if deleted."""
        ...
