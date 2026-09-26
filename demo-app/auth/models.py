"""User and Role models."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship

from database import Base


# Association table for user-role many-to-many
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
)


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", secondary=user_roles, back_populates="roles")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    roles = relationship("Role", secondary=user_roles, back_populates="users")
    # Explicitly specify foreign_keys for owner relationship
    tasks = relationship("Task", foreign_keys="Task.owner_id", back_populates="owner")
    assigned_tasks = relationship("Task", foreign_keys="Task.assignee_id", back_populates="assignee")

    def verify_password(self, password: str) -> bool:
        """Verify password against hash (simplified for demo)."""
        # In production, use bcrypt/argon2
        return self.hashed_password == f"hashed_{password}"

    def get_role_names(self) -> list[str]:
        return [role.name for role in self.roles]