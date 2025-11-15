"""
FastAPI application exposing the same functionality as the CLI.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from lib.database import init_db
from services.contact_service import ContactService
from services.note_service import NoteService
from services.organization_service import OrganizationService
from services.task_service import TaskService

# Initialize database
init_db()

app = FastAPI(
    title="Commands API",
    description="Contact, Organization, Note, and Task management API",
    version="0.1.0",
)


# Pydantic models for request/response
class ContactCreate(BaseModel):
    first_name: str
    last_name: str


class ContactResponse(BaseModel):
    id: int
    first_name: str
    last_name: str

    class Config:
        from_attributes = True


class ContactWithNoteCount(BaseModel):
    id: int
    first_name: str
    last_name: str
    note_count: int


class OrganizationCreate(BaseModel):
    name: str


class OrganizationResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class OrganizationWithNoteCount(BaseModel):
    id: int
    name: str
    note_count: int


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: datetime
    importance: int = Field(ge=0, le=10, default=0)
    contact_ids: Optional[List[int]] = None
    organization_ids: Optional[List[int]] = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    due_date: datetime
    importance: int
    completed: int
    created_at: datetime
    updated_at: datetime
    contacts: List[ContactResponse] = []
    organizations: List[OrganizationResponse] = []

    class Config:
        from_attributes = True


class NoteCreate(BaseModel):
    title: str
    content: str
    contact_ids: Optional[List[int]] = None
    organization_ids: Optional[List[int]] = None
    task_ids: Optional[List[int]] = None


class NoteResponse(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    contacts: List[ContactResponse] = []
    organizations: List[OrganizationResponse] = []

    class Config:
        from_attributes = True


class TagUpdate(BaseModel):
    add_contact_ids: Optional[List[int]] = None
    remove_contact_ids: Optional[List[int]] = None
    add_organization_ids: Optional[List[int]] = None
    remove_organization_ids: Optional[List[int]] = None
    add_task_ids: Optional[List[int]] = None
    remove_task_ids: Optional[List[int]] = None


# Contact endpoints
@app.post("/contacts", response_model=ContactResponse, status_code=201)
def create_contact(contact: ContactCreate):
    """Add a new contact."""
    result, error = ContactService.add_contact(contact.first_name, contact.last_name)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return result


@app.get("/contacts", response_model=List[ContactResponse])
def list_contacts():
    """List all contacts."""
    return ContactService.list_contacts()


@app.get("/contacts/top", response_model=List[ContactWithNoteCount])
def get_top_contacts(limit: int = 10):
    """Get top contacts by note count."""
    results = ContactService.get_top_contacts(limit)
    return [
        ContactWithNoteCount(
            id=contact.id,
            first_name=contact.first_name,
            last_name=contact.last_name,
            note_count=note_count,
        )
        for contact, note_count in results
    ]


@app.get("/contacts/search", response_model=List[ContactResponse])
def search_contacts(query: str):
    """Search contacts by name."""
    return ContactService.search_contacts(query)


@app.post("/contacts/bulk", response_model=dict)
def bulk_add_contacts(names: List[str]):
    """Add multiple contacts at once."""
    added, skipped = ContactService.bulk_add_contacts(names)
    return {"added": added, "skipped": skipped}


# Organization endpoints
@app.post("/organizations", response_model=OrganizationResponse, status_code=201)
def create_organization(organization: OrganizationCreate):
    """Add a new organization."""
    result, error = OrganizationService.add_organization(organization.name)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return result


@app.get("/organizations", response_model=List[OrganizationResponse])
def list_organizations():
    """List all organizations."""
    return OrganizationService.list_organizations()


@app.get("/organizations/top", response_model=List[OrganizationWithNoteCount])
def get_top_organizations(limit: int = 10):
    """Get top organizations by note count."""
    results = OrganizationService.get_top_organizations(limit)
    return [
        OrganizationWithNoteCount(
            id=org.id,
            name=org.name,
            note_count=note_count,
        )
        for org, note_count in results
    ]


# Task endpoints
@app.post("/tasks", response_model=TaskResponse, status_code=201)
def create_task(task: TaskCreate):
    """Add a new task."""
    result, error = TaskService.add_task(
        title=task.title,
        due_date=task.due_date,
        importance=task.importance,
        description=task.description,
        contact_ids=task.contact_ids,
        organization_ids=task.organization_ids,
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    return result


@app.get("/tasks", response_model=List[TaskResponse])
def list_tasks(
    limit: int = 20,
    show_completed: bool = False,
    contact_id: Optional[int] = None,
    organization_id: Optional[int] = None,
):
    """List tasks with optional filtering."""
    return TaskService.list_tasks(limit, show_completed, contact_id, organization_id)


@app.get("/tasks/urgent", response_model=List[TaskResponse])
def get_urgent_tasks(days: int = 7, sort_by: str = "urgency"):
    """Get tasks due within a certain timeframe."""
    if sort_by not in ["urgency", "importance"]:
        raise HTTPException(
            status_code=400, detail="sort_by must be 'urgency' or 'importance'"
        )
    return TaskService.get_urgent_tasks(days, sort_by)


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int):
    """Get a specific task."""
    task = TaskService.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@app.post("/tasks/{task_id}/complete", response_model=TaskResponse)
def complete_task(task_id: int):
    """Mark a task as completed."""
    task, error = TaskService.complete_task(task_id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return task


@app.post("/tasks/{task_id}/uncomplete", response_model=TaskResponse)
def uncomplete_task(task_id: int):
    """Mark a task as incomplete."""
    task, error = TaskService.uncomplete_task(task_id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return task


@app.patch("/tasks/{task_id}/tags", response_model=dict)
def update_task_tags(task_id: int, tags: TagUpdate):
    """Add or remove tags from a task."""
    changes, error = TaskService.tag_task(
        task_id,
        add_contact_ids=tags.add_contact_ids,
        add_org_ids=tags.add_organization_ids,
        remove_contact_ids=tags.remove_contact_ids,
        remove_org_ids=tags.remove_organization_ids,
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    return changes


# Note endpoints
@app.post("/notes", response_model=NoteResponse, status_code=201)
def create_note(note: NoteCreate):
    """Add a new note."""
    result, error = NoteService.add_note(
        title=note.title,
        content=note.content,
        contact_ids=note.contact_ids,
        organization_ids=note.organization_ids,
        task_ids=note.task_ids,
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    return result


@app.get("/notes", response_model=List[NoteResponse])
def list_notes(
    limit: int = 20,
    contact_id: Optional[int] = None,
    organization_id: Optional[int] = None,
):
    """List notes with optional filtering."""
    notes, error = NoteService.list_notes(limit, contact_id, organization_id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return notes


@app.get("/notes/{note_id}", response_model=NoteResponse)
def get_note(note_id: int):
    """Get a specific note."""
    note = NoteService.get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail=f"Note {note_id} not found")
    return note


@app.patch("/notes/{note_id}/tags", response_model=dict)
def update_note_tags(note_id: int, tags: TagUpdate):
    """Add or remove tags from a note."""
    changes, error = NoteService.tag_note(
        note_id,
        add_contact_ids=tags.add_contact_ids,
        remove_contact_ids=tags.remove_contact_ids,
        add_org_ids=tags.add_organization_ids,
        remove_org_ids=tags.remove_organization_ids,
        add_task_ids=tags.add_task_ids,
        remove_task_ids=tags.remove_task_ids,
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    return changes


@app.get("/")
def root():
    """API root endpoint."""
    return {
        "message": "Commands API",
        "version": "0.1.0",
        "endpoints": {
            "contacts": "/contacts",
            "organizations": "/organizations",
            "tasks": "/tasks",
            "notes": "/notes",
            "docs": "/docs",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
