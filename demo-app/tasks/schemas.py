"""Pydantic schemas for tasks - contains BUG API-003."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator
from tasks.models import TaskPriority, TaskStatus


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.OPEN
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[datetime] = None
    assignee_id: Optional[int] = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    priority: TaskPriority
    status: TaskStatus
    owner_id: int
    assignee_id: Optional[int]
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TaskAssignRequest(BaseModel):
    user_id: int


# BUG API-003: Invalid priority value causes 500 instead of 422
# The priority field uses TaskPriority enum but validation error
# is not properly caught, causing internal server error
# instead of 422 Unprocessable Entity

# The bug is that the field_validator for priority is missing
# Pydantic v2 should handle enum validation automatically,
# but the error handling in the endpoint doesn't catch validation errors properly

class TaskFilterParams(BaseModel):
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee_id: Optional[int] = None
    page: int = 1
    page_size: int = 20

    @field_validator("page")
    @classmethod
    def page_must_be_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Page must be >= 1")
        return v

    @field_validator("page_size")
    @classmethod
    def page_size_must_be_reasonable(cls, v: int) -> int:
        if v < 1 or v > 100:
            raise ValueError("Page size must be between 1 and 100")
        return v