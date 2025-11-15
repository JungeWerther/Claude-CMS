"""
Task model for managing tasks with due dates and importance scores.

A Task represents a task with a title, description, due date, and importance score.
Tasks can be associated with Contacts and Organizations (many-to-many).
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship

from models import ValidatedBase, ValidatedPydanticModel

# Association table for many-to-many relationship between Task and Contact
task_contact_association = Table(
    "task_contact_association",
    ValidatedBase.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id"), primary_key=True),
    Column("contact_id", Integer, ForeignKey("contacts.id"), primary_key=True),
)

# Association table for many-to-many relationship between Task and Organization
task_organization_association = Table(
    "task_organization_association",
    ValidatedBase.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id"), primary_key=True),
    Column(
        "organization_id", Integer, ForeignKey("organizations.id"), primary_key=True
    ),
)


# ========== SQLAlchemy Models ==========


class Task(ValidatedBase):
    """SQLAlchemy Task model."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=False)
    importance = Column(Integer, nullable=False, default=0)  # 0-10 scale
    completed = Column(
        Integer, nullable=False, default=0
    )  # 0 = not completed, 1 = completed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationship to contacts (many-to-many)
    contacts = relationship(
        "Contact",
        secondary=task_contact_association,
        back_populates="tasks",
    )

    # Relationship to organizations (many-to-many)
    organizations = relationship(
        "Organization",
        secondary=task_organization_association,
        back_populates="tasks",
    )

    # Relationship to notes (many-to-many)
    notes = relationship(
        "Note",
        secondary="note_task_association",
        back_populates="tasks",
    )


# Store reference to SQLAlchemy Task before it gets overwritten
TaskDB = Task


# ========== Pydantic Models ==========


class Task(ValidatedPydanticModel):
    """Pydantic Task model for validation and serialization."""

    id: Optional[int] = Field(default=None, description="Task ID")
    title: str = Field(..., description="Task title", max_length=200)
    description: Optional[str] = Field(default=None, description="Task description")
    due_date: datetime = Field(..., description="Task due date")
    importance: int = Field(
        default=0, description="Task importance score (0-10)", ge=0, le=10
    )
    completed: bool = Field(default=False, description="Task completion status")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    contact_ids: List[int] = Field(
        default_factory=list, description="List of contact IDs tagged in this task"
    )
    organization_ids: List[int] = Field(
        default_factory=list,
        description="List of organization IDs tagged in this task",
    )


# Store reference to Pydantic Task
TaskSchema = Task


# ========== Extended Models with Relationships ==========


class TaskBasic(BaseModel):
    """Basic task information without relationships."""

    model_config = {"from_attributes": True}

    id: Optional[int] = Field(default=None, description="Task ID")
    title: str = Field(..., description="Task title", max_length=200)
    description: Optional[str] = Field(default=None, description="Task description")
    due_date: datetime = Field(..., description="Task due date")
    importance: int = Field(
        default=0, description="Task importance score (0-10)", ge=0, le=10
    )
    completed: bool = Field(default=False, description="Task completion status")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )


# Export both DB and Schema versions
__all__ = [
    "TaskDB",
    "TaskSchema",
    "TaskBasic",
]
