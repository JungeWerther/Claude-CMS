"""
Note service layer - business logic for note operations.
"""

from typing import List, Optional, Tuple

from sqlalchemy import select

from lib.database import get_db_session
from models.contact_note import ContactDB, NoteDB, OrganizationDB
from models.task import TaskDB
from services.base_service import is_remote_mode


class NoteService:
    """Service for note-related operations."""

    @staticmethod
    def add_note(
        title: str,
        content: str,
        contact_ids: Optional[List[int]] = None,
        organization_ids: Optional[List[int]] = None,
        task_ids: Optional[List[int]] = None,
    ) -> Tuple[Optional[NoteDB], Optional[str]]:
        """
        Add a new note with optional tags.

        Returns:
            Tuple of (note, error_message). If error occurs, note is None.
        """
        # If in remote mode, use HTTP client
        if is_remote_mode():
            from services.http_client import NoteHTTP

            return NoteHTTP.add_note(
                title, content, contact_ids, organization_ids, task_ids
            )

        with get_db_session() as session:
            # Create new note
            note = NoteDB(title=title, content=content)

            # Add contact associations
            if contact_ids:
                stmt = select(ContactDB).where(ContactDB.id.in_(contact_ids))
                contact_objs = session.execute(stmt).scalars().all()

                found_ids = {c.id for c in contact_objs}
                missing_ids = set(contact_ids) - found_ids

                if missing_ids:
                    return (
                        None,
                        f"Contact IDs not found: {', '.join(map(str, missing_ids))}",
                    )

                note.contacts.extend(contact_objs)

            # Add organization associations
            if organization_ids:
                stmt = select(OrganizationDB).where(
                    OrganizationDB.id.in_(organization_ids)
                )
                organization_objs = session.execute(stmt).scalars().all()

                found_ids = {o.id for o in organization_objs}
                missing_ids = set(organization_ids) - found_ids

                if missing_ids:
                    return (
                        None,
                        f"Organization IDs not found: {', '.join(map(str, missing_ids))}",
                    )

                note.organizations.extend(organization_objs)

            # Add task associations
            if task_ids:
                stmt = select(TaskDB).where(TaskDB.id.in_(task_ids))
                task_objs = session.execute(stmt).scalars().all()

                found_ids = {t.id for t in task_objs}
                missing_ids = set(task_ids) - found_ids

                if missing_ids:
                    return (
                        None,
                        f"Task IDs not found: {', '.join(map(str, missing_ids))}",
                    )

                note.tasks.extend(task_objs)

            session.add(note)
            session.flush()
            session.refresh(note, ["contacts", "organizations", "tasks"])

            return note, None

    @staticmethod
    def list_notes(
        limit: int = 20,
        contact_id: Optional[int] = None,
        organization_id: Optional[int] = None,
    ) -> Tuple[Optional[List[NoteDB]], Optional[str]]:
        """
        List notes with optional filtering.

        Returns:
            Tuple of (notes_list, error_message)
        """
        # If in remote mode, use HTTP client
        if is_remote_mode():
            from services.http_client import NoteHTTP

            return NoteHTTP.list_notes(limit, contact_id, organization_id)

        with get_db_session() as session:
            if contact_id:
                stmt = select(ContactDB).where(ContactDB.id == contact_id)
                contact = session.execute(stmt).scalar_one_or_none()

                if not contact:
                    return None, f"Contact ID {contact_id} not found"

                notes_list = contact.notes[:limit]
            elif organization_id:
                stmt = select(OrganizationDB).where(
                    OrganizationDB.id == organization_id
                )
                organization = session.execute(stmt).scalar_one_or_none()

                if not organization:
                    return None, f"Organization ID {organization_id} not found"

                notes_list = organization.notes[:limit]
            else:
                stmt = select(NoteDB).order_by(NoteDB.created_at.desc()).limit(limit)
                notes_list = session.execute(stmt).scalars().all()

            # Refresh relationships
            for note in notes_list:
                session.refresh(note, ["contacts", "organizations", "tasks"])

            return notes_list, None

    @staticmethod
    def get_note(note_id: int) -> Optional[NoteDB]:
        """Get a single note by ID."""
        # If in remote mode, use HTTP client
        if is_remote_mode():
            from services.http_client import NoteHTTP

            return NoteHTTP.get_note(note_id)

        with get_db_session() as session:
            stmt = select(NoteDB).where(NoteDB.id == note_id)
            note = session.execute(stmt).scalar_one_or_none()

            if note:
                session.refresh(note, ["contacts", "organizations", "tasks"])

            return note

    @staticmethod
    def tag_note(
        note_id: int,
        add_contact_ids: Optional[List[int]] = None,
        remove_contact_ids: Optional[List[int]] = None,
        add_org_ids: Optional[List[int]] = None,
        remove_org_ids: Optional[List[int]] = None,
        add_task_ids: Optional[List[int]] = None,
        remove_task_ids: Optional[List[int]] = None,
    ) -> Tuple[Optional[dict], Optional[str]]:
        """
        Add or remove tags from a note.

        Returns:
            Tuple of (changes_dict, error_message)
        """
        # If in remote mode, use HTTP client
        if is_remote_mode():
            from services.http_client import NoteHTTP

            return NoteHTTP.tag_note(
                note_id,
                add_contact_ids,
                remove_contact_ids,
                add_org_ids,
                remove_org_ids,
                add_task_ids,
                remove_task_ids,
            )

        with get_db_session() as session:
            stmt = select(NoteDB).where(NoteDB.id == note_id)
            note = session.execute(stmt).scalar_one_or_none()

            if not note:
                return None, f"Note ID {note_id} not found"

            session.refresh(note, ["contacts", "organizations", "tasks"])

            changes = {
                "added_contacts": [],
                "removed_contacts": [],
                "added_organizations": [],
                "removed_organizations": [],
                "added_tasks": [],
                "removed_tasks": [],
            }

            # Add contacts
            if add_contact_ids:
                stmt = select(ContactDB).where(ContactDB.id.in_(add_contact_ids))
                contacts_to_add = session.execute(stmt).scalars().all()

                found_ids = {c.id for c in contacts_to_add}
                missing_ids = set(add_contact_ids) - found_ids

                if missing_ids:
                    return (
                        None,
                        f"Contact IDs not found: {', '.join(map(str, missing_ids))}",
                    )

                existing_ids = {c.id for c in note.contacts}
                new_contacts = [c for c in contacts_to_add if c.id not in existing_ids]

                if new_contacts:
                    note.contacts.extend(new_contacts)
                    changes["added_contacts"] = [
                        f"{c.first_name} {c.last_name}" for c in new_contacts
                    ]

            # Remove contacts
            if remove_contact_ids:
                contacts_to_remove = [
                    c for c in note.contacts if c.id in remove_contact_ids
                ]
                if contacts_to_remove:
                    for contact in contacts_to_remove:
                        note.contacts.remove(contact)
                    changes["removed_contacts"] = [
                        f"{c.first_name} {c.last_name}" for c in contacts_to_remove
                    ]

            # Add organizations
            if add_org_ids:
                stmt = select(OrganizationDB).where(OrganizationDB.id.in_(add_org_ids))
                organizations_to_add = session.execute(stmt).scalars().all()

                found_ids = {o.id for o in organizations_to_add}
                missing_ids = set(add_org_ids) - found_ids

                if missing_ids:
                    return (
                        None,
                        f"Organization IDs not found: {', '.join(map(str, missing_ids))}",
                    )

                existing_ids = {o.id for o in note.organizations}
                new_organizations = [
                    o for o in organizations_to_add if o.id not in existing_ids
                ]

                if new_organizations:
                    note.organizations.extend(new_organizations)
                    changes["added_organizations"] = [o.name for o in new_organizations]

            # Remove organizations
            if remove_org_ids:
                organizations_to_remove = [
                    o for o in note.organizations if o.id in remove_org_ids
                ]
                if organizations_to_remove:
                    for organization in organizations_to_remove:
                        note.organizations.remove(organization)
                    changes["removed_organizations"] = [
                        o.name for o in organizations_to_remove
                    ]

            # Add tasks
            if add_task_ids:
                stmt = select(TaskDB).where(TaskDB.id.in_(add_task_ids))
                tasks_to_add = session.execute(stmt).scalars().all()

                found_ids = {t.id for t in tasks_to_add}
                missing_ids = set(add_task_ids) - found_ids

                if missing_ids:
                    return (
                        None,
                        f"Task IDs not found: {', '.join(map(str, missing_ids))}",
                    )

                existing_ids = {t.id for t in note.tasks}
                new_tasks = [t for t in tasks_to_add if t.id not in existing_ids]

                if new_tasks:
                    note.tasks.extend(new_tasks)
                    changes["added_tasks"] = [t.title for t in new_tasks]

            # Remove tasks
            if remove_task_ids:
                tasks_to_remove = [t for t in note.tasks if t.id in remove_task_ids]
                if tasks_to_remove:
                    for task in tasks_to_remove:
                        note.tasks.remove(task)
                    changes["removed_tasks"] = [t.title for t in tasks_to_remove]

            session.flush()

            return changes, None
