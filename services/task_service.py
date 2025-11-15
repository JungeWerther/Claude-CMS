"""
Task service layer - business logic for task operations.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy import select

from lib.database import get_db_session
from models.contact_note import ContactDB, OrganizationDB
from models.task import TaskDB


class TaskService:
    """Service for task-related operations."""

    @staticmethod
    def add_task(
        title: str,
        due_date: datetime,
        importance: int,
        description: Optional[str] = None,
        contact_ids: Optional[List[int]] = None,
        organization_ids: Optional[List[int]] = None,
    ) -> Tuple[Optional[TaskDB], Optional[str]]:
        """
        Add a new task.

        Returns:
            Tuple of (task, error_message). If error occurs, task is None.
        """
        # Validate importance
        if importance < 0 or importance > 10:
            return None, "Importance must be between 0 and 10"

        with get_db_session() as session:
            # Create task
            task = TaskDB(
                title=title,
                description=description,
                due_date=due_date,
                importance=importance,
            )
            session.add(task)
            session.flush()

            # Add contact tags
            if contact_ids:
                stmt = select(ContactDB).where(ContactDB.id.in_(contact_ids))
                contact_objs = session.execute(stmt).scalars().all()
                task.contacts.extend(contact_objs)

            # Add organization tags
            if organization_ids:
                stmt = select(OrganizationDB).where(
                    OrganizationDB.id.in_(organization_ids)
                )
                org_objs = session.execute(stmt).scalars().all()
                task.organizations.extend(org_objs)

            session.flush()
            session.refresh(task, ["contacts", "organizations"])

            return task, None

    @staticmethod
    def list_tasks(
        limit: int = 20,
        show_completed: bool = False,
        contact_id: Optional[int] = None,
        organization_id: Optional[int] = None,
    ) -> List[TaskDB]:
        """List tasks with optional filtering."""
        with get_db_session() as session:
            stmt = select(TaskDB).order_by(TaskDB.due_date.asc())

            if not show_completed:
                stmt = stmt.where(TaskDB.completed == 0)

            if contact_id:
                stmt = stmt.join(TaskDB.contacts).where(ContactDB.id == contact_id)

            if organization_id:
                stmt = stmt.join(TaskDB.organizations).where(
                    OrganizationDB.id == organization_id
                )

            stmt = stmt.limit(limit)
            tasks = session.execute(stmt).scalars().all()

            # Refresh relationships
            for task in tasks:
                session.refresh(task, ["contacts", "organizations"])

            return tasks

    @staticmethod
    def get_urgent_tasks(days: int = 7, sort_by: str = "urgency") -> List[TaskDB]:
        """Get tasks due within a certain timeframe."""
        with get_db_session() as session:
            now = datetime.utcnow()
            threshold = now + timedelta(days=days)

            stmt = select(TaskDB).where(
                TaskDB.completed == 0, TaskDB.due_date <= threshold
            )

            if sort_by == "urgency":
                stmt = stmt.order_by(TaskDB.due_date.asc())
            else:
                stmt = stmt.order_by(TaskDB.importance.desc(), TaskDB.due_date.asc())

            tasks = session.execute(stmt).scalars().all()

            # Refresh relationships
            for task in tasks:
                session.refresh(task, ["contacts", "organizations"])

            return tasks

    @staticmethod
    def get_task(task_id: int) -> Optional[TaskDB]:
        """Get a single task by ID."""
        with get_db_session() as session:
            stmt = select(TaskDB).where(TaskDB.id == task_id)
            task = session.execute(stmt).scalar_one_or_none()

            if task:
                session.refresh(task, ["contacts", "organizations"])

            return task

    @staticmethod
    def complete_task(task_id: int) -> Tuple[Optional[TaskDB], Optional[str]]:
        """Mark a task as completed."""
        with get_db_session() as session:
            stmt = select(TaskDB).where(TaskDB.id == task_id)
            task = session.execute(stmt).scalar_one_or_none()

            if not task:
                return None, f"Task with ID {task_id} not found"

            if task.completed:
                return None, f"Task '{task.title}' is already completed"

            task.completed = 1
            session.flush()
            session.refresh(task)

            return task, None

    @staticmethod
    def uncomplete_task(task_id: int) -> Tuple[Optional[TaskDB], Optional[str]]:
        """Mark a task as incomplete."""
        with get_db_session() as session:
            stmt = select(TaskDB).where(TaskDB.id == task_id)
            task = session.execute(stmt).scalar_one_or_none()

            if not task:
                return None, f"Task with ID {task_id} not found"

            if not task.completed:
                return None, f"Task '{task.title}' is already incomplete"

            task.completed = 0
            session.flush()
            session.refresh(task)

            return task, None

    @staticmethod
    def tag_task(
        task_id: int,
        add_contact_ids: Optional[List[int]] = None,
        add_org_ids: Optional[List[int]] = None,
        remove_contact_ids: Optional[List[int]] = None,
        remove_org_ids: Optional[List[int]] = None,
    ) -> Tuple[Optional[dict], Optional[str]]:
        """
        Add or remove tags from a task.

        Returns:
            Tuple of (changes_dict, error_message)
        """
        with get_db_session() as session:
            stmt = select(TaskDB).where(TaskDB.id == task_id)
            task = session.execute(stmt).scalar_one_or_none()

            if not task:
                return None, f"Task with ID {task_id} not found"

            session.refresh(task, ["contacts", "organizations"])

            changes = {
                "added_contacts": [],
                "removed_contacts": [],
                "added_organizations": [],
                "removed_organizations": [],
            }

            # Add contacts
            if add_contact_ids:
                stmt = select(ContactDB).where(ContactDB.id.in_(add_contact_ids))
                contacts_to_add = session.execute(stmt).scalars().all()
                for contact in contacts_to_add:
                    if contact not in task.contacts:
                        task.contacts.append(contact)
                        changes["added_contacts"].append(
                            f"{contact.first_name} {contact.last_name}"
                        )

            # Remove contacts
            if remove_contact_ids:
                task.contacts = [
                    c for c in task.contacts if c.id not in remove_contact_ids
                ]
                stmt = select(ContactDB).where(ContactDB.id.in_(remove_contact_ids))
                removed_contact_objs = session.execute(stmt).scalars().all()
                changes["removed_contacts"] = [
                    f"{c.first_name} {c.last_name}" for c in removed_contact_objs
                ]

            # Add organizations
            if add_org_ids:
                stmt = select(OrganizationDB).where(OrganizationDB.id.in_(add_org_ids))
                orgs_to_add = session.execute(stmt).scalars().all()
                for org in orgs_to_add:
                    if org not in task.organizations:
                        task.organizations.append(org)
                        changes["added_organizations"].append(org.name)

            # Remove organizations
            if remove_org_ids:
                task.organizations = [
                    o for o in task.organizations if o.id not in remove_org_ids
                ]
                stmt = select(OrganizationDB).where(
                    OrganizationDB.id.in_(remove_org_ids)
                )
                removed_org_objs = session.execute(stmt).scalars().all()
                changes["removed_organizations"] = [o.name for o in removed_org_objs]

            session.flush()

            return changes, None
