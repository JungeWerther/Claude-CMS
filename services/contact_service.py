"""
Contact service layer - business logic for contact operations.
"""

from typing import List, Optional, Tuple

from sqlalchemy import func, select

from lib.database import get_db_session
from models.contact_note import ContactDB, NoteDB


class ContactService:
    """Service for contact-related operations."""

    @staticmethod
    def add_contact(
        first_name: str, last_name: str
    ) -> Tuple[Optional[ContactDB], Optional[str]]:
        """
        Add a new contact.

        Returns:
            Tuple of (contact, error_message). If error occurs, contact is None.
        """
        with get_db_session() as session:
            # Check if contact already exists
            stmt = select(ContactDB).where(
                ContactDB.first_name == first_name,
                ContactDB.last_name == last_name,
            )
            existing = session.execute(stmt).scalar_one_or_none()

            if existing:
                return (
                    None,
                    f"Contact '{first_name} {last_name}' already exists (ID: {existing.id})",
                )

            # Create new contact
            contact = ContactDB(first_name=first_name, last_name=last_name)
            session.add(contact)
            session.flush()
            session.refresh(contact)

            return contact, None

    @staticmethod
    def list_contacts() -> List[ContactDB]:
        """List all contacts ordered by last name."""
        with get_db_session() as session:
            stmt = select(ContactDB).order_by(ContactDB.last_name)
            return session.execute(stmt).scalars().all()

    @staticmethod
    def get_top_contacts(limit: int = 10) -> List[Tuple[ContactDB, int]]:
        """
        Get top N contacts by note count.

        Returns:
            List of tuples (contact, note_count)
        """
        with get_db_session() as session:
            stmt = (
                select(ContactDB, func.count(NoteDB.id).label("note_count"))
                .outerjoin(ContactDB.notes)
                .group_by(ContactDB.id)
                .order_by(func.count(NoteDB.id).desc())
                .limit(limit)
            )
            return session.execute(stmt).all()

    @staticmethod
    def bulk_add_contacts(names: List[str]) -> Tuple[List[str], List[str]]:
        """
        Add multiple contacts at once.

        Args:
            names: List of names in format "FirstName LastName" or "FirstName"

        Returns:
            Tuple of (added_names, skipped_names)
        """
        with get_db_session() as session:
            added = []
            skipped = []

            for name in names:
                parts = name.strip().split(maxsplit=1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ""

                # Check if contact already exists
                stmt = select(ContactDB).where(
                    ContactDB.first_name == first_name,
                    ContactDB.last_name == last_name,
                )
                existing = session.execute(stmt).scalar_one_or_none()

                if existing:
                    skipped.append(f"{first_name} {last_name} (ID: {existing.id})")
                else:
                    contact = ContactDB(first_name=first_name, last_name=last_name)
                    session.add(contact)
                    session.flush()
                    added.append(f"{first_name} {last_name} (ID: {contact.id})")

            return added, skipped

    @staticmethod
    def search_contacts(query: str) -> List[ContactDB]:
        """Search contacts by first name or last name."""
        with get_db_session() as session:
            query_lower = query.lower()

            stmt = (
                select(ContactDB)
                .where(
                    (func.lower(ContactDB.first_name).contains(query_lower))
                    | (func.lower(ContactDB.last_name).contains(query_lower))
                )
                .order_by(ContactDB.first_name, ContactDB.last_name)
            )

            return session.execute(stmt).scalars().all()

    @staticmethod
    def get_contact_with_notes(
        contact_id: int, note_limit: int = 10
    ) -> Optional[Tuple[ContactDB, List[NoteDB]]]:
        """
        Get a contact with their recent notes.

        Returns:
            Tuple of (contact, notes) or None if contact not found
        """
        with get_db_session() as session:
            stmt = select(ContactDB).where(ContactDB.id == contact_id)
            contact = session.execute(stmt).scalar_one_or_none()

            if not contact:
                return None

            session.refresh(contact, ["notes"])
            last_notes = sorted(
                contact.notes, key=lambda n: n.created_at, reverse=True
            )[:note_limit]

            return contact, last_notes
