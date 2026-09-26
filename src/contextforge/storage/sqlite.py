"""SQLite storage implementation using sqlite-utils."""

import json
from pathlib import Path
from typing import Any

import sqlite_utils

from contextforge.config import get_config
from contextforge.models import ContextIR, ContextItem, ContextType, ItemStatus
from contextforge.models.debugging_state import DebuggingState


class SQLiteStore:
    """SQLite-backed context store."""

    def __init__(self, db_path: Path | None = None) -> None:
        config = get_config()
        self.db_path = db_path or config.database_path
        self.db: sqlite_utils.Database | None = None

    def initialize(self) -> None:
        """Initialize database and create tables."""
        self.db = sqlite_utils.Database(self.db_path)

        # Context items table
        self.db["context_items"].create(  # type: ignore[union-attr]
            {
                "id": str,
                "type": str,
                "content": str,
                "source": str,
                "importance": float,
                "freshness": float,
                "status": str,
                "created_at": str,
                "updated_at": str,
                "provenance": str,  # JSON
                "tags": str,  # JSON array
                "metadata": str,  # JSON
                "task_id": str,
            },
            pk="id",
            if_not_exists=True,
        )
        self.db["context_items"].create_index(["task_id"], if_not_exists=True)  # type: ignore[union-attr]
        self.db["context_items"].create_index(["type"], if_not_exists=True)  # type: ignore[union-attr]
        self.db["context_items"].create_index(["status"], if_not_exists=True)  # type: ignore[union-attr]

        # Context IR table
        self.db["context_ir"].create(  # type: ignore[union-attr]
            {
                "id": str,
                "version": str,
                "task_id": str,
                "task_description": str,
                "items": str,  # JSON array of item IDs
                "created_at": str,
                "updated_at": str,
                "metadata": str,  # JSON
            },
            pk="id",
            if_not_exists=True,
        )
        self.db["context_ir"].create_index(["task_id"], if_not_exists=True)  # type: ignore[union-attr]

        # Debugging state table
        self.db["debugging_states"].create(  # type: ignore[union-attr]
            {
                "task_id": str,
                "task_description": str,
                "current_hypothesis": str,
                "confirmed_facts": str,  # JSON array
                "evidence": str,  # JSON array
                "rejected_hypotheses": str,  # JSON
                "open_questions": str,  # JSON array
                "relevant_files": str,  # JSON array
                "previous_actions": str,  # JSON
                "status": str,
                "created_at": str,
                "updated_at": str,
                "metadata": str,  # JSON
            },
            pk="task_id",
            if_not_exists=True,
        )

    def close(self) -> None:
        """Close database connection."""
        if self.db:
            self.db.close()
            self.db = None

    def _ensure_db(self) -> sqlite_utils.Database:
        if self.db is None:
            self.initialize()
        assert self.db is not None
        return self.db

    # ContextItem operations
    def put_item(self, item: ContextItem) -> None:
        db = self._ensure_db()
        db["context_items"].upsert(  # type: ignore[union-attr]
            {
                "id": item.id,
                "type": item.type.value,
                "content": item.content,
                "source": item.source,
                "importance": item.importance,
                "freshness": item.freshness,
                "status": item.status.value,
                "created_at": item.created_at.isoformat(),
                "updated_at": item.updated_at.isoformat(),
                "provenance": item.provenance.model_dump_json(),
                "tags": json.dumps(list(item.tags)),
                "metadata": json.dumps(item.metadata),
                "task_id": item.provenance.task_id or "",
            },
            pk="id",
        )

    def get_item(self, item_id: str) -> ContextItem | None:
        db = self._ensure_db()
        try:
            row = db["context_items"].get(item_id)  # type: ignore[union-attr]
        except sqlite_utils.db.NotFoundError:
            return None
        return self._row_to_item(row)

    def delete_item(self, item_id: str) -> bool:
        db = self._ensure_db()
        try:
            db["context_items"].delete(item_id)  # type: ignore[union-attr]
            return True
        except sqlite_utils.db.NotFoundError:
            return False

    def list_items(
        self,
        type_: str | None = None,
        status: str | None = None,
        task_id: str | None = None,
        tags: list[str] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ContextItem]:
        db = self._ensure_db()
        query = "SELECT * FROM context_items WHERE 1=1"
        params: list[Any] = []

        if type_:
            query += " AND type = ?"
            params.append(type_)
        if status:
            query += " AND status = ?"
            params.append(status)
        if task_id:
            query += " AND task_id = ?"
            params.append(task_id)

        query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = db.query(query, params)
        items = [self._row_to_item(row) for row in rows]

        if tags:
            items = [item for item in items if any(tag in item.tags for tag in tags)]

        return items

    # ContextIR operations
    def put_ir(self, ir: ContextIR) -> None:
        db = self._ensure_db()
        db["context_ir"].upsert(  # type: ignore[union-attr]
            {
                "id": ir.id,
                "version": ir.version,
                "task_id": ir.task_id,
                "task_description": ir.task_description,
                "items": json.dumps([item.id for item in ir.items]),
                "created_at": ir.created_at.isoformat(),
                "updated_at": ir.updated_at.isoformat(),
                "metadata": json.dumps(ir.metadata),
            },
            pk="id",
        )
        # Also store all items
        for item in ir.items:
            self.put_item(item)

    def get_ir(self, ir_id: str) -> ContextIR | None:
        db = self._ensure_db()
        row = db["context_ir"].get(ir_id)  # type: ignore[union-attr]
        if not row:
            return None
        return self._row_to_ir(row)

    def get_ir_by_task(self, task_id: str) -> ContextIR | None:
        db = self._ensure_db()
        rows = list(db["context_ir"].rows_where("task_id = ?", [task_id], order_by="-updated_at"))
        if not rows:
            return None
        return self._row_to_ir(rows[0])

    def delete_ir(self, ir_id: str) -> bool:
        db = self._ensure_db()
        try:
            db["context_ir"].delete(ir_id)  # type: ignore[union-attr]
            return True
        except sqlite_utils.db.NotFoundError:
            return False

    # DebuggingState operations
    def put_state(self, state: DebuggingState) -> None:
        db = self._ensure_db()
        import json as json_module

        db["debugging_states"].upsert(  # type: ignore[union-attr]
            {
                "task_id": state.task_id,
                "task_description": state.task_description,
                "current_hypothesis": state.current_hypothesis or "",
                "confirmed_facts": json_module.dumps(state.confirmed_facts),
                "evidence": json_module.dumps(state.evidence),
                "rejected_hypotheses": json_module.dumps(
                    [h.model_dump(mode="json") for h in state.rejected_hypotheses]
                ),
                "open_questions": json_module.dumps(state.open_questions),
                "relevant_files": json_module.dumps(state.relevant_files),
                "previous_actions": json_module.dumps(
                    [a.model_dump(mode="json") for a in state.previous_actions]
                ),
                "status": state.status.value,
                "created_at": state.created_at.isoformat(),
                "updated_at": state.updated_at.isoformat(),
                "metadata": json_module.dumps(state.metadata),
            },
            pk="task_id",
        )

    def get_state(self, task_id: str) -> DebuggingState | None:
        db = self._ensure_db()
        try:
            row = db["debugging_states"].get(task_id)  # type: ignore[union-attr]
        except sqlite_utils.db.NotFoundError:
            return None
        return self._row_to_state(row)

    def delete_state(self, task_id: str) -> bool:
        db = self._ensure_db()
        try:
            db["debugging_states"].delete(task_id)  # type: ignore[union-attr]
            return True
        except sqlite_utils.db.NotFoundError:
            return False

    # Helpers
    def _row_to_item(self, row: dict[str, Any]) -> ContextItem:
        from contextforge.models.provenance import Provenance
        provenance = Provenance.model_validate_json(row["provenance"])
        return ContextItem(
            id=row["id"],
            type=ContextType(row["type"]),
            content=row["content"],
            source=row["source"],
            importance=row["importance"],
            freshness=row["freshness"],
            status=ItemStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            provenance=provenance,
            tags=set(json.loads(row["tags"])),
            metadata=json.loads(row["metadata"]),
        )

    def _row_to_ir(self, row: dict[str, Any]) -> ContextIR:
        item_ids = json.loads(row["items"])
        items = []
        for item_id in item_ids:
            item = self.get_item(item_id)
            if item:
                items.append(item)
        return ContextIR(
            id=row["id"],
            version=row["version"],
            task_id=row["task_id"],
            task_description=row["task_description"],
            items=items,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            metadata=json.loads(row["metadata"]),
        )

    def _row_to_state(self, row: dict[str, Any]) -> DebuggingState:
        import json as json_module

        from contextforge.models.debugging_state import Action, DebuggingStatus, RejectedHypothesis

        rejected = [
            RejectedHypothesis.model_validate(h)
            for h in json_module.loads(row["rejected_hypotheses"])
        ]
        actions = [
            Action.model_validate(a) for a in json_module.loads(row["previous_actions"])
        ]
        return DebuggingState(
            task_id=row["task_id"],
            task_description=row["task_description"],
            current_hypothesis=row["current_hypothesis"] or None,
            confirmed_facts=json_module.loads(row["confirmed_facts"]),
            evidence=json_module.loads(row["evidence"]),
            rejected_hypotheses=rejected,
            open_questions=json_module.loads(row["open_questions"]),
            relevant_files=json_module.loads(row["relevant_files"]),
            previous_actions=actions,
            status=DebuggingStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            metadata=json_module.loads(row["metadata"]),
        )
