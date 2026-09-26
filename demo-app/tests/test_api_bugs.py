"""Tests for BUG API-003: Invalid priority causes 500 instead of 422."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestBugAPI003:
    """Tests for BUG API-003: Invalid priority value causes 500 instead of 422."""

    def test_create_task_invalid_priority_returns_422(self, client, auth_headers):
        """Test that invalid priority returns 422, not 500."""
        response = client.post(
            "/tasks",
            json={
                "title": "Test Task",
                "description": "Test",
                "priority": "invalid_priority"  # Not in enum
            },
            headers=auth_headers
        )
        # Should return 422 Unprocessable Entity, not 500
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data

    def test_update_task_invalid_priority_returns_422(self, client, auth_headers, db_session):
        """Test that updating with invalid priority returns 422."""
        from tasks.service import TaskService
        from tasks.schemas import TaskCreate
        service = TaskService(db_session)
        task = service.create_task(TaskCreate(title="Test"), owner_id=1)

        response = client.patch(
            f"/tasks/{task.id}",
            json={"priority": "not_a_valid_priority"},
            headers=auth_headers
        )
        # Should return 422, not 500
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"

    def test_valid_priority_accepted(self, client, auth_headers):
        """Test that valid priorities are accepted."""
        for priority in ["low", "medium", "high", "urgent"]:
            response = client.post(
                "/tasks",
                json={
                    "title": f"Task {priority}",
                    "priority": priority
                },
                headers=auth_headers
            )
            assert response.status_code == 201, f"Priority '{priority}' should be valid: {response.text}"