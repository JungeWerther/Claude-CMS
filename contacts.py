"""
Contact management CLI commands.
"""

import click

from lib.database import init_db
from services.contact_service import ContactService


@click.group()
def contacts():
    """Manage contacts and notes."""
    # Ensure database is initialized
    init_db()


@contacts.command()
@click.option("--first-name", "-f", required=True, help="Contact's first name")
@click.option("--last-name", "-l", required=True, help="Contact's last name")
def add(first_name: str, last_name: str):
    """Add a new contact to the database."""
    contact, error = ContactService.add_contact(first_name, last_name)

    if error:
        click.echo(f"❌ {error}", err=True)
        return

    click.echo(f"✅ Contact added: {first_name} {last_name} (ID: {contact.id})")


@contacts.command()
@click.option(
    "--limit",
    "-n",
    default=10,
    type=int,
    help="Number of top contacts to display (default: 10)",
)
def top(limit: int):
    """
    Get the top N contacts with the most notes associated with them.
    """
    results = ContactService.get_top_contacts(limit)

    if not results:
        click.echo("No contacts found.")
        return

    click.echo(f"\n📊 Top {limit} Contacts by Note Count:\n")
    click.echo(f"{'ID':<6} {'Name':<30} {'Notes':<10}")
    click.echo("-" * 50)

    for contact, note_count in results:
        full_name = f"{contact.first_name} {contact.last_name}"
        click.echo(f"{contact.id:<6} {full_name:<30} {note_count:<10}")


@contacts.command()
def list():
    """List all contacts."""
    all_contacts = ContactService.list_contacts()

    if not all_contacts:
        click.echo("No contacts found.")
        return

    click.echo(f"\n📇 All Contacts ({len(all_contacts)}):\n")
    click.echo(f"{'ID':<6} {'First Name':<20} {'Last Name':<20}")
    click.echo("-" * 50)

    for contact in all_contacts:
        click.echo(f"{contact.id:<6} {contact.first_name:<20} {contact.last_name:<20}")


@contacts.command()
@click.argument("names", nargs=-1, required=True)
def bulk_add(names):
    """
    Add multiple contacts at once.

    Usage:
        python main.py contacts bulk-add "John Doe" "Jane Smith" "Bob"

    Each name can be:
    - "FirstName LastName" (both names)
    - "FirstName" (first name only, last name will be empty)
    """
    added, skipped = ContactService.bulk_add_contacts(list(names))

    if added:
        click.echo(f"✅ Added {len(added)} contact(s):")
        for name in added:
            click.echo(f"   • {name}")

    if skipped:
        click.echo(f"\n⚠️  Skipped {len(skipped)} existing contact(s):")
        for name in skipped:
            click.echo(f"   • {name}")


@contacts.command()
@click.argument("query", required=True)
def search(query):
    """
    Search contacts by first name, last name, or both.

    Usage:
        python main.py contacts search "john"
        python main.py contacts search "doe"
    """
    results = ContactService.search_contacts(query)

    if not results:
        click.echo(f"No contacts found matching '{query}'")
        return

    click.echo(f"\n🔍 Found {len(results)} contact(s) matching '{query}':\n")
    click.echo(f"{'ID':<6} {'First Name':<20} {'Last Name':<20}")
    click.echo("-" * 50)

    for contact in results:
        click.echo(f"{contact.id:<6} {contact.first_name:<20} {contact.last_name:<20}")


@contacts.command()
def init():
    """Initialize context: show top 10 contacts and their last 10 notes each."""
    top_contacts = ContactService.get_top_contacts(10)

    if not top_contacts:
        click.echo("No contacts found.")
        return

    click.echo("\n" + "=" * 80)
    click.echo("📊 TOP 10 CONTACTS BY NOTE COUNT")
    click.echo("=" * 80 + "\n")

    for contact, note_count in top_contacts:
        click.echo(f"\n{'─' * 80}")
        click.echo(
            f"👤 {contact.first_name} {contact.last_name} (ID: {contact.id}) - {note_count} note(s)"
        )
        click.echo(f"{'─' * 80}\n")

        # Get last 10 notes for this contact
        result = ContactService.get_contact_with_notes(contact.id, note_limit=10)

        if result:
            _, last_notes = result
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
    contacts()
