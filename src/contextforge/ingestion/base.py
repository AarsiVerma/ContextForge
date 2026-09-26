"""Ingestion interface - ContextSource protocol."""

from typing import Protocol

from contextforge.models import ContextItem


class ContextSource(Protocol):
    """Protocol for context sources."""

    def fetch(self) -> list[ContextItem]:
        """Fetch context items from this source."""
        ...

    def name(self) -> str:
        """Return source identifier."""
        ...
