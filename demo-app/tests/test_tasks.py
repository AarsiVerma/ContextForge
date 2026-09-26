"""Tests for tasks - BUG DB-002, API-003, INT-005."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock
import threading
import time

from tasks.service import TaskService
from tasks.schemas import TaskCreate, TaskUpdate, TaskFilterParams
from tasks.models import Task, TaskAssignment, TaskPriority, TaskStatus
from auth.models import User


class TestTaskService:
    """Test task service operations."""

    def test_create_task(self, db_session):
        """Test creating a task."""
        service = TaskService(db_session)
        task_data = TaskCreate(
            title="Test Task",
            description="Test description",
            priority=TaskPriority.HIGH
        )
        task = service.create_task(task_data, owner_id=1)
        assert task.id is not None
        assert task.title == "Test Task"
        assert task.priority == TaskPriority.HIGH
        assert task.owner_id == 1

    def test_get_task(self, db_session):
        """Test getting a task by ID."""
        service = TaskService(db_session)
        task_data = TaskCreate(title="Test Task")
        created = service.create_task(task_data, owner_id=1)

        task = service.get_task(created.id)
        assert task is not None
        assert task.id == created.id

    def test_list_tasks(self, db_session):
        """Test listing tasks."""
        service = TaskService(db_session)
        for i in range(5):
            service.create_task(TaskCreate(title=f"Task {i}"), owner_id=1)

        from tasks.schemas import TaskFilterParams
        tasks, total = service.list_tasks(TaskFilterParams(page=1, page_size=10))
        assert total == 5
        assert len(tasks) == 5

    def test_update_task(self, db_session):
        """Test updating a task."""
        service = TaskService(db_session)
        task = service.create_task(TaskCreate(title="Original"), owner_id=1)

        from tasks.schemas import TaskUpdate
        updated = service.update_task(task.id, TaskUpdate(title="Updated"))
        assert updated.title == "Updated"

    def test_delete_task(self, db_session):
        """Test deleting a task."""
        service = TaskService(db_session)
        task = service.create_task(TaskCreate(title="To Delete"), owner_id=1)
        result = service.delete_task(task.id)
        assert result is True
        assert service.get_task(task.id) is None


class TestBugDB002:
    """Tests for BUG DB-002: Race condition in task assignment."""

    def test_concurrent_assignment_race_condition(self, db_session):
        """Test that demonstrates the race condition in task assignment."""
        service = TaskService(db_session)

        # Create a task
        task = service.create_task(TaskCreate(title="Race Task"), owner_id=1)

        # Create two users
        user1 = User(username="user1", email="user1@test.com", hashed_password="hash1")
        user2 = User(username="user2", email="user2@test.com", hashed_password="hash2")
        db_session.add_all([user1, user2])
        db_session.commit()
        db_session.refresh(user1)
        db_session.refresh(user2)

        # Track results
        results = {"user1": None, "user2": None}
        errors = {"user1": None, "user2": None}

        def assign_task(user, key):
            try:
                service = TaskService(db_session)
                # Use same task_id
                assignment = service.assign_task(1, user.id, 1)
                results[key] = assignment
            except Exception as e:
                errors[key] = e

        # Run concurrent assignments
        thread1 = threading.Thread(target=assign_task, args=(user1, "user1"))
        thread2 = threading.Thread(target=assign_task, args=(user2, "user2"))

        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

        # BUG: Both assignments might succeed due to race condition
        # At least one should fail, but both might succeed
        success_count = sum(1 for r in results.values() if r is not None)
        # With the bug, both might succeed (race condition)
        # After fix, only one should succeed
        print(f"Successful assignments: {success_count}")
        print(f"Errors: {errors}")

    def test_assign_task_success(self, db_session):
        """Test successful task assignment."""
        service = TaskService(db_session)
        task = service.create_task(TaskCreate(title="Assignable"), owner_id=1)

        user = User(username="assignee", email="assignee@test.com", hashed_password="hash")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assignment = service.assign_task(task.id, user.id, 1)
        assert assignment is not None
        assert assignment.task_id == task.id
        assert assignment.user_id == user.id

    def test_assign_already_assigned_task(self, db_session):
        """Test assigning already assigned task fails."""
        service = TaskService(db_session)
        task = service.create_task(TaskCreate(title="Assignable"), owner_id=1)

        user1 = User(username="user1", email="u1@test.com", hashed_password="hash")
        user2 = User(username="user2", email="u2@test.com", hashed_password="hash")
        db_session.add_all([user1, user2])
        db_session.commit()
        db_session.refresh(user1)
        db_session.refresh(user2)

        # First assignment
        service.assign_task(task.id, user1.id, 1)

        # Second assignment should fail
        with pytest.raises(ValueError, match="already assigned"):
            service.assign_task(task.id, user2.id, 1)