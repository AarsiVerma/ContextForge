"""Tests for BUG INT-005: Pagination bug and CACHE-004: Stale permissions."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from tasks.service import TaskService
from tasks.schemas import TaskFilterParams, TaskCreate
from tasks.models import Task, TaskPriority, TaskStatus
from auth.models import User, Role


class TestBugINT005:
    """Tests for BUG INT-005: Pagination returns duplicates."""

    def test_pagination_no_duplicates(self, db_session):
        """Test that pagination doesn't return duplicate items."""
        service = TaskService(db_session)

        # Create 25 tasks with same status
        for i in range(25):
            service.create_task(
                TaskCreate(title=f"Task {i}", status=TaskStatus.OPEN),
                owner_id=1
            )

        from tasks.schemas import TaskFilterParams
        # Get page 1
        page1_tasks, _ = service.list_tasks(TaskFilterParams(page=1, page_size=10, status=TaskStatus.OPEN))
        page1_ids = {t.id for t in page1_tasks}

        # Get page 2
        page2_tasks, _ = service.list_tasks(TaskFilterParams(page=2, page_size=10, status=TaskStatus.OPEN))
        page2_ids = {t.id for t in page2_tasks}

        # BUG INT-005: Duplicates between pages
        intersection = page1_ids & page2_ids
        assert len(intersection) == 0, f"Duplicate tasks between pages: {intersection}"

        # Total unique should be 20 (10 per page)
        all_ids = page1_ids | page2_ids
        assert len(all_ids) == 20, f"Expected 20 unique tasks, got {len(all_ids)}"

    def test_pagination_order_consistency(self, db_session):
        """Test that pagination order is consistent."""
        service = TaskService(db_session)

        for i in range(15):
            service.create_task(
                TaskCreate(title=f"Task {i}", status=TaskStatus.OPEN),
                owner_id=1
            )

        from tasks.schemas import TaskFilterParams
        page1, _ = service.list_tasks(TaskFilterParams(page=1, page_size=10, status=TaskStatus.OPEN))
        page2, _ = service.list_tasks(TaskFilterParams(page=2, page_size=10, status=TaskStatus.OPEN))

        # All page 1 IDs should be less than page 2 IDs (if ordered by ID)
        page1_max = max(t.id for t in page1)
        page2_min = min(t.id for t in page2)
        # With proper ordering, page1_max < page2_min
        # BUG INT-005: Missing ORDER BY causes non-deterministic ordering
        # This test documents the expected behavior
        assert page1_max < page2_min, "Pagination order should be consistent (by ID)"


class TestBugCACHE004:
    """Tests for BUG CACHE-004: Stale user permissions in JWT."""

    def test_permission_change_not_reflected_immediately(self, client, db_session):
        """Test that permission changes aren't reflected until token refresh."""
        from auth.token import create_access_token, validate_access_token
        from auth.models import Role

        # Create user and admin role
        user = User(username="permuser", email="perm@test.com", hashed_password="hashed_pass")
        admin_role = Role(name="admin", description="Administrator")
        db_session.add_all([user, admin_role])
        db_session.commit()
        db_session.refresh(user)

        # Create token WITHOUT admin role
        token = create_access_token({"sub": user.username, "user_id": user.id, "roles": ["user"]})
        headers = {"Authorization": f"Bearer {token}"}

        # Grant admin role
        admin_role = db_session.query(Role).filter(Role.name == "admin").first()
        user.roles.append(admin_role)
        db_session.commit()

        # Try to access admin-only endpoint with old token
        # The token still has old roles ["user"] - BUG CACHE-004
        payload = validate_access_token(token)
        # The payload contains old roles, not updated ones
        assert "admin" not in payload.get("roles", [])

    def test_token_contains_roles_at_issuance(self):
        """Test that JWT contains roles at issuance time only."""
        from auth.token import create_access_token, validate_access_token

        token = create_access_token({"sub": "testuser", "user_id": 1, "roles": ["user"]})
        payload = validate_access_token(token)

        assert "roles" in payload
        assert payload["roles"] == ["user"]

    def test_role_change_requires_new_token(self):
        """Test that role changes require new token issuance."""
        from auth.token import create_access_token

        # Token issued with user role
        token = create_access_token({"sub": "testuser", "user_id": 1, "roles": ["user"]})

        # Even if DB roles change, token still has old roles
        # This is the expected behavior of stateless JWTs
        # BUG CACHE-004: Application doesn't handle this