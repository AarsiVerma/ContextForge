"""Context IR - canonical intermediate representation."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from contextforge.models.context_item import ContextItem, ContextType, ItemStatus


class ContextIR(BaseModel):
    """Canonical context intermediate representation."""

    version: str = "0.1.0"
    id: str = Field(default_factory=lambda: str(uuid4()))
    task_id: str
    task_description: str
    items: list[ContextItem] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_item(self, item: ContextItem) -> None:
        """Add a context item."""
        self.items.append(item)
        self.updated_at = datetime.utcnow()

    def get_items_by_type(self, type_: "ContextType") -> list[ContextItem]:
        """Get all items of a specific type."""
        return [item for item in self.items if item.type == type_]

    def get_items_by_status(self, status: "ItemStatus") -> list[ContextItem]:
        """Get all items with a specific status."""
        return [item for item in self.items if item.status == status]

    def get_item(self, item_id: str) -> ContextItem | None:
        """Get item by ID."""
        for item in self.items:
            if item.id == item_id:
                return item
        return None

    def remove_item(self, item_id: str) -> bool:
        """Remove item by ID."""
        for i, item in enumerate(self.items):
            if item.id == item_id:
                self.items.pop(i)
                self.updated_at = datetime.utcnow()
                return True
        return False

    def to_json(self) -> str:
        """Serialize to JSON."""
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ContextIR":
        """Deserialize from JSON."""
        return cls.model_validate_json(json_str)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContextIR":
        """Create from dictionary."""
        return cls.model_validate(data)
