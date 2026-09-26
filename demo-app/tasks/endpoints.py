"""Task endpoints - contains BUG API-003."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import get_db
from auth.models import User
from auth.token import validate_access_token
from auth.endpoints import oauth2_scheme
from tasks.service import TaskService
from tasks.schemas import (
    TaskCreate, TaskUpdate, TaskResponse, TaskListResponse,
    TaskAssignRequest, TaskFilterParams
)
from tasks.models import TaskPriority, TaskStatus

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    """Extract user ID from access token."""
    payload = validate_access_token(token)
    return payload.get("user_id")


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: "TaskCreate",
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Create a new task."""
    from tasks.schemas import TaskCreate
    service = TaskService(db)
    task = service.create_task(task_data, owner_id=user_id)
    return task


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[TaskStatus] = Query(None),
    priority: Optional[TaskPriority] = Query(None),
    assignee_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List tasks with filtering and pagination. BUG INT-005: pagination bug."""
    filters = TaskFilterParams(
        status=status,
        priority=priority,
        assignee_id=assignee_id,
        page=page,
        page_size=page_size,
    )
    service = TaskService(db)
    tasks, total = service.list_tasks(filters)

    total_pages = (total + filters.page_size - 1) // filters.page_size

    return TaskListResponse(
        tasks=tasks,
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        total_pages=total_pages
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a task by ID."""
    service = TaskService(db)
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: "TaskUpdate",
    db: Session = Depends(get_db),
):
    """Update a task."""
    from tasks.schemas import TaskUpdate
    service = TaskService(db)
    task = service.update_task(task_id, task_data)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task."""
    service = TaskService(db)
    if not service.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")


# BUG API-003: Invalid priority value causes 500 instead of 422
# The endpoint doesn't properly catch Pydantic validation errors
# causing internal server error instead of 422
@router.post("/{task_id}/assign", response_model=dict)
async def assign_task(
    task_id: int,
    assign_data: TaskAssignRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Assign task to user. BUG DB-002: race condition."""
    service = TaskService(db)
    try:
        assignment = service.assign_task(task_id, assign_data.user_id, user_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Task or user not found")
        return {"message": "Task assigned successfully", "assignment_id": assignment.id}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Task already assigned")


@router.post("/{task_id}/unassign", response_model=dict)
async def unassign_task(
    task_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Unassign task from current user."""
    service = TaskService(db)
    if not service.unassign_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found or not assigned")
    return {"message": "Task unassigned successfully"}


@router.patch("/{task_id}/status", response_model=TaskResponse)
async def change_task_status(
    task_id: int,
    new_status: TaskStatus,
    db: Session = Depends(get_db),
):
    """Change task status."""
    service = TaskService(db)
    task = service.change_status(task_id, new_status)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task