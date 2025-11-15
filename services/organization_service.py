"""
Organization service layer - business logic for organization operations.
"""

from typing import List, Optional, Tuple

from sqlalchemy import func, select

from lib.database import get_db_session
from models.contact_note import NoteDB, OrganizationDB


class OrganizationService:
    """Service for organization-related operations."""

    @staticmethod
    def add_organization(name: str) -> Tuple[Optional[OrganizationDB], Optional[str]]:
        """
        Add a new organization.

        Returns:
            Tuple of (organization, error_message). If error occurs, organization is None.
        """
        with get_db_session() as session:
            # Check if organization already exists
            stmt = select(OrganizationDB).where(OrganizationDB.name == name)
            existing = session.execute(stmt).scalar_one_or_none()

            if existing:
                return None, f"Organization '{name}' already exists (ID: {existing.id})"

            # Create new organization
            organization = OrganizationDB(name=name)
            session.add(organization)
            session.flush()
            session.refresh(organization)

            return organization, None

    @staticmethod
    def list_organizations() -> List[OrganizationDB]:
        """List all organizations ordered by name."""
        with get_db_session() as session:
            stmt = select(OrganizationDB).order_by(OrganizationDB.name)
            return session.execute(stmt).scalars().all()

    @staticmethod
    def get_top_organizations(limit: int = 10) -> List[Tuple[OrganizationDB, int]]:
        """
        Get top N organizations by note count.

        Returns:
            List of tuples (organization, note_count)
        """
        with get_db_session() as session:
            stmt = (
                select(OrganizationDB, func.count(NoteDB.id).label("note_count"))
                .outerjoin(OrganizationDB.notes)
                .group_by(OrganizationDB.id)
                .order_by(func.count(NoteDB.id).desc())
                .limit(limit)
            )
            return session.execute(stmt).all()
