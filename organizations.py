"""
Organization management CLI commands.
"""

import click

from lib.database import init_db
from services.organization_service import OrganizationService


@click.group()
def organizations():
    """Manage organizations and notes."""
    # Ensure database is initialized
    init_db()


@organizations.command()
@click.option("--name", "-n", required=True, help="Organization name")
def add(name: str):
    """Add a new organization to the database."""
    organization, error = OrganizationService.add_organization(name)

    if error:
        click.echo(f"❌ {error}", err=True)
        return

    click.echo(f"✅ Organization added: {name} (ID: {organization.id})")


@organizations.command()
@click.option(
    "--limit",
    "-n",
    default=10,
    type=int,
    help="Number of top organizations to display (default: 10)",
)
def top(limit: int):
    """
    Get the top N organizations with the most notes associated with them.
    """
    results = OrganizationService.get_top_organizations(limit)

    if not results:
        click.echo("No organizations found.")
        return

    click.echo(f"\n📊 Top {limit} Organizations by Note Count:\n")
    click.echo(f"{'ID':<6} {'Name':<40} {'Notes':<10}")
    click.echo("-" * 60)

    for organization, note_count in results:
        click.echo(f"{organization.id:<6} {organization.name:<40} {note_count:<10}")


@organizations.command()
def list():
    """List all organizations."""
    all_organizations = OrganizationService.list_organizations()

    if not all_organizations:
        click.echo("No organizations found.")
        return

    click.echo(f"\n🏢 All Organizations ({len(all_organizations)}):\n")
    click.echo(f"{'ID':<6} {'Name':<40}")
    click.echo("-" * 50)

    for organization in all_organizations:
        click.echo(f"{organization.id:<6} {organization.name:<40}")


@organizations.command()
@click.argument("names", nargs=-1, required=True)
def bulk_add(names):
    """
    Add multiple organizations at once.

    Usage:
        python main.py organizations bulk-add "Acme Corp" "Tech Startup Inc" "University"

    Each name will be added as a separate organization.
    """
    added = []
    skipped = []

    for name in names:
        name = name.strip()
        organization, error = OrganizationService.add_organization(name)

        if error:
            skipped.append(f"{name}")
        else:
            added.append(f"{name} (ID: {organization.id})")

    if added:
        click.echo(f"✅ Added {len(added)} organization(s):")
        for name in added:
            click.echo(f"   • {name}")

    if skipped:
        click.echo(f"\n⚠️  Skipped {len(skipped)} existing organization(s):")
        for name in skipped:
            click.echo(f"   • {name}")


@organizations.command()
@click.argument("query", required=True)
def search(query):
    """
    Search organizations by name.

    Usage:
        python main.py organizations search "tech"
        python main.py organizations search "university"
    """
    # For search, we can add it to the service layer
    from sqlalchemy import func, select

    from lib.database import get_db_session
    from models.contact_note import OrganizationDB

    with get_db_session() as session:
        query_lower = query.lower()
        stmt = (
            select(OrganizationDB)
            .where(func.lower(OrganizationDB.name).contains(query_lower))
            .order_by(OrganizationDB.name)
        )
        results = session.execute(stmt).scalars().all()

    if not results:
        click.echo(f"No organizations found matching '{query}'")
        return

    click.echo(f"\n🔍 Found {len(results)} organization(s) matching '{query}':\n")
    click.echo(f"{'ID':<6} {'Name':<40}")
    click.echo("-" * 50)

    for organization in results:
        click.echo(f"{organization.id:<6} {organization.name:<40}")


@organizations.command()
def init():
    """Initialize context: show top 10 organizations and their last 10 notes each."""
    top_organizations = OrganizationService.get_top_organizations(10)

    if not top_organizations:
        click.echo("No organizations found.")
        return

    click.echo("\n" + "=" * 80)
    click.echo("📊 TOP 10 ORGANIZATIONS BY NOTE COUNT")
    click.echo("=" * 80 + "\n")

    from lib.database import get_db_session

    with get_db_session() as session:
        for organization, note_count in top_organizations:
            click.echo(f"\n{'─' * 80}")
            click.echo(
                f"🏢 {organization.name} (ID: {organization.id}) - {note_count} note(s)"
            )
            click.echo(f"{'─' * 80}\n")

            # Get last 10 notes for this organization
            session.refresh(organization, ["notes"])
            last_notes = sorted(
                organization.notes, key=lambda n: n.created_at, reverse=True
            )[:10]

            if last_notes:
                for i, note in enumerate(last_notes, 1):
                    click.echo(f"  📝 Note {i} (ID: {note.id})")
                    click.echo(f"     Title: {note.title}")
                    click.echo(
                        f"     Created: {note.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    click.echo(f"     Content: {note.content[:100]}...")
                    if len(note.content) > 100:
                        click.echo(
                            f"              [{len(note.content) - 100} more characters]"
                        )
                    click.echo()
            else:
                click.echo("  (No notes found)\n")

    click.echo("=" * 80 + "\n")


if __name__ == "__main__":
    organizations()
