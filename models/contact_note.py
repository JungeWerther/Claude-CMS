"""
Contact and Note models with many-to-many relationship.

A Contact represents a person with first and last name.
A Note can be associated with multiple Contacts (many-to-many).

Note: To satisfy the metaclass validation while avoiding namespace collisions,
we define SQLAlchemy models first, then redefine them as Pydantic models.
Import the models from their respective sections using qualified imports.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship

from models import ValidatedBase, ValidatedPydanticModel

if TYPE_CHECKING:
    pass


# Association table for many-to-many relationship between Note and Contact
note_contact_association = Table(
    "note_contact_association",
    ValidatedBase.metadata,
    Column("note_id", Integer, ForeignKey("notes.id"), primary_key=True),
    Column("contact_id", Integer, ForeignKey("contacts.id"), primary_key=True),
)

# Association table for many-to-many relationship between Note and Organization
note_organization_association = Table(
    "note_organization_association",
    ValidatedBase.metadata,
    Column("note_id", Integer, ForeignKey("notes.id"), primary_key=True),
    Column(
        "organization_id", Integer, ForeignKey("organizations.id"), primary_key=True
    ),
)

# Association table for many-to-many relationship between Note and Task
note_task_association = Table(
    "note_task_association",
    ValidatedBase.metadata,
    Column("note_id", Integer, ForeignKey("notes.id"), primary_key=True),
    Column("task_id", Integer, ForeignKey("tasks.id"), primary_key=True),
)


# ========== SQLAlchemy Models ==========


class Contact(ValidatedBase):
    """SQLAlchemy Contact model."""

    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)

    # Relationship to notes (many-to-many)
    notes = relationship(
        "Note",
        secondary=note_contact_association,
        back_populates="contacts",
    )

    # Relationship to tasks (many-to-many)
    tasks = relationship(
        "Task",
        secondary="task_contact_association",
        back_populates="contacts",
    )


# Store reference to SQLAlchemy Contact before it gets overwritten
ContactDB = Contact


class Organization(ValidatedBase):
    """SQLAlchemy Organization model."""

    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True)

    # Relationship to notes (many-to-many)
    notes = relationship(
        "Note",
        secondary=note_organization_association,
        back_populates="organizations",
    )

    # Relationship to tasks (many-to-many)
    tasks = relationship(
        "Task",
        secondary="task_organization_association",
        back_populates="organizations",
    )


# Store reference to SQLAlchemy Organization before it gets overwritten
OrganizationDB = Organization


class Note(ValidatedBase):
    """SQLAlchemy Note model."""

    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationship to contacts (many-to-many)
    contacts = relationship(
        "Contact",
        secondary=note_contact_association,
        back_populates="notes",
    )

    # Relationship to organizations (many-to-many)
    organizations = relationship(
        "Organization",
        secondary=note_organization_association,
        back_populates="notes",
    )

    # Relationship to tasks (many-to-many)
    tasks = relationship(
        "Task",
        secondary=note_task_association,
        back_populates="notes",
    )


# Store reference to SQLAlchemy Note before it gets overwritten
NoteDB = Note


# ========== Pydantic Models ==========


class Contact(ValidatedPydanticModel):
    """Pydantic Contact model for validation and serialization."""

    id: Optional[int] = Field(default=None, description="Contact ID")
    first_name: str = Field(..., description="Contact's first name", max_length=100)
    last_name: str = Field(..., description="Contact's last name", max_length=100)


# Store reference to Pydantic Contact
ContactSchema = Contact


class Organization(ValidatedPydanticModel):
    """Pydantic Organization model for validation and serialization."""

    id: Optional[int] = Field(default=None, description="Organization ID")
    name: str = Field(..., description="Organization name", max_length=200)


# Store reference to Pydantic Organization
OrganizationSchema = Organization


class Note(ValidatedPydanticModel):
    """Pydantic Note model for validation and serialization."""

    id: Optional[int] = Field(default=None, description="Note ID")
    title: str = Field(..., description="Note title", max_length=200)
    content: str = Field(..., description="Note content")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    contact_ids: List[int] = Field(
        default_factory=list, description="List of contact IDs tagged in this note"
    )
    organization_ids: List[int] = Field(
        default_factory=list, description="List of organization IDs tagged in this note"
    )


# Store reference to Pydantic Note
NoteSchema = Note


# ========== Extended Models with Relationships ==========


class ContactWithNotes(BaseModel):
    """Contact model with associated notes included."""

    model_config = {"from_attributes": True}

    id: Optional[int] = Field(default=None, description="Contact ID")
    first_name: str = Field(..., description="Contact's first name", max_length=100)
    last_name: str = Field(..., description="Contact's last name", max_length=100)
    notes: List["NoteBasic"] = Field(
        default_factory=list, description="Notes associated with this contact"
    )


class NoteBasic(BaseModel):
    """Basic note information without contacts (to avoid circular reference)."""

    model_config = {"from_attributes": True}

    id: Optional[int] = Field(default=None, description="Note ID")
    title: str = Field(..., description="Note title", max_length=200)
    content: str = Field(..., description="Note content")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )


class OrganizationWithNotes(BaseModel):
    """Organization model with associated notes included."""

    model_config = {"from_attributes": True}

    id: Optional[int] = Field(default=None, description="Organization ID")
    name: str = Field(..., description="Organization name", max_length=200)
    notes: List["NoteBasic"] = Field(
        default_factory=list, description="Notes associated with this organization"
    )


class NoteWithContacts(BaseModel):
    """Note model with associated contacts included."""

    model_config = {"from_attributes": True}

    id: Optional[int] = Field(default=None, description="Note ID")
    title: str = Field(..., description="Note title", max_length=200)
    content: str = Field(..., description="Note content")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    contacts: List[ContactSchema] = Field(
        default_factory=list, description="Contacts tagged in this note"
    )
    organizations: List[OrganizationSchema] = Field(
        default_factory=list, description="Organizations tagged in this note"
    )


# Export both DB and Schema versions
__all__ = [
    "ContactDB",
    "NoteDB",
    "OrganizationDB",
    "ContactSchema",
    "NoteSchema",
    "OrganizationSchema",
    "ContactWithNotes",
    "OrganizationWithNotes",
    "NoteBasic",
    "NoteWithContacts",
]
