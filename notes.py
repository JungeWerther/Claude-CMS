"""
Note management CLI commands.
"""

import click

from lib.database import init_db
from services.note_service import NoteService


@click.group()
def notes():
    """Manage notes and their contact associations."""
    # Ensure database is initialized
    init_db()


@notes.command()
@click.option("--title", "-t", required=True, help="Note title")
@click.option("--content", "-c", required=True, help="Note content")
@click.option(
    "--contacts",
    "-C",
    multiple=True,
    type=int,
    help="Contact IDs to tag (can be specified multiple times)",
)
@click.option(
    "--organizations",
    "-O",
    multiple=True,
    type=int,
    help="Organization IDs to tag (can be specified multiple times)",
)
@click.option(
    "--tasks",
    "-T",
    multiple=True,
    type=int,
    help="Task IDs to tag (can be specified multiple times)",
)
def add(title: str, content: str, contacts: tuple, organizations: tuple, tasks: tuple):
    """Add a new note with optional contact and organization references."""
    note, error = NoteService.add_note(
        title=title,
        content=content,
        contact_ids=list(contacts) if contacts else None,
        organization_ids=list(organizations) if organizations else None,
        task_ids=list(tasks) if tasks else None,
    )

    if error:
        click.echo(f"❌ {error}", err=True)
        return

    # Display confirmation
    tags = []
    if note.contacts:
        contact_names = [f"{c.first_name} {c.last_name}" for c in note.contacts]
        tags.append(f"Contacts: {', '.join(contact_names)}")
    if note.organizations:
        org_names = [o.name for o in note.organizations]
        tags.append(f"Organizations: {', '.join(org_names)}")
    if note.tasks:
        task_titles = [t.title for t in note.tasks]
        tags.append(f"Tasks: {', '.join(task_titles)}")

    if tags:
        click.echo(
            f"✅ Note added: '{title}' (ID: {note.id}) - Tagged: {' | '.join(tags)}"
        )
    else:
        click.echo(f"✅ Note added: '{title}' (ID: {note.id})")


@notes.command()
@click.option(
    "--limit",
    "-n",
    default=20,
    type=int,
    help="Number of notes to display (default: 20)",
)
@click.option(
    "--contact-id",
    "-c",
    type=int,
    help="Filter by contact ID",
)
@click.option(
    "--organization-id",
    "-o",
    type=int,
    help="Filter by organization ID",
)
def list(limit: int, contact_id: int, organization_id: int):
    """List notes with optional filtering by contact or organization."""
    notes_list, error = NoteService.list_notes(limit, contact_id, organization_id)

    if error:
        click.echo(f"❌ {error}", err=True)
        return

    if contact_id:
        click.echo(
            f"\n📝 Notes for contact ID {contact_id} (showing {len(notes_list)}):\n"
        )
    elif organization_id:
        click.echo(
            f"\n📝 Notes for organization ID {organization_id} (showing {len(notes_list)}):\n"
        )
    else:
        click.echo(f"\n📝 Recent Notes (showing {len(notes_list)}):\n")

    if not notes_list:
        click.echo("No notes found.")
        return

    click.echo(f"{'ID':<6} {'Title':<30} {'C':<4} {'O':<4} {'T':<4} {'Created':<20}")
    click.echo("-" * 74)

    for note in notes_list:
        contact_count = len(note.contacts)
        org_count = len(note.organizations)
        task_count = len(note.tasks)
        created_str = note.created_at.strftime("%Y-%m-%d %H:%M")
        title_short = note.title[:27] + "..." if len(note.title) > 30 else note.title
        click.echo(
            f"{note.id:<6} {title_short:<30} {contact_count:<4} {org_count:<4} {task_count:<4} {created_str:<20}"
        )


@notes.command()
@click.argument("note_id", type=int)
def view(note_id: int):
    """View a note with full details including tagged contacts and organizations."""
    note = NoteService.get_note(note_id)

    if not note:
        click.echo(f"❌ Note ID {note_id} not found", err=True)
        return

    # Display note details
    click.echo(f"\n{'=' * 60}")
    click.echo(f"📝 Note ID: {note.id}")
    click.echo(f"{'=' * 60}")
    click.echo(f"Title: {note.title}")
    click.echo(f"Created: {note.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    click.echo(f"Updated: {note.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    click.echo(f"\n{'-' * 60}")
    click.echo("Content:")
    click.echo(f"{'-' * 60}")
    click.echo(note.content)
    click.echo(f"{'-' * 60}\n")

    if note.contacts:
        click.echo("👥 Tagged Contacts:")
        for contact in note.contacts:
            click.echo(
                f"  • {contact.first_name} {contact.last_name} (ID: {contact.id})"
            )
    else:
        click.echo("👥 Tagged Contacts: None")

    if note.organizations:
        click.echo("\n🏢 Tagged Organizations:")
        for organization in note.organizations:
            click.echo(f"  • {organization.name} (ID: {organization.id})")
    else:
        click.echo("\n🏢 Tagged Organizations: None")

    if note.tasks:
        click.echo("\n📋 Tagged Tasks:")
        for task in note.tasks:
            status = "✅" if task.completed else "⏳"
            click.echo(f"  • {status} {task.title} (ID: {task.id})")
    else:
        click.echo("\n📋 Tagged Tasks: None")

    click.echo(f"\n{'=' * 60}\n")


@notes.command()
@click.argument("note_id", type=int)
@click.option(
    "--add-contact",
    "-a",
    multiple=True,
    type=int,
    help="Contact IDs to add to the note (can be specified multiple times)",
)
@click.option(
    "--remove-contact",
    "-r",
    multiple=True,
    type=int,
    help="Contact IDs to remove from the note (can be specified multiple times)",
)
@click.option(
    "--add-organization",
    "-A",
    multiple=True,
    type=int,
    help="Organization IDs to add to the note (can be specified multiple times)",
)
@click.option(
    "--remove-organization",
    "-R",
    multiple=True,
    type=int,
    help="Organization IDs to remove from the note (can be specified multiple times)",
)
@click.option(
    "--add-task",
    "-t",
    multiple=True,
    type=int,
    help="Task IDs to add to the note (can be specified multiple times)",
)
@click.option(
    "--remove-task",
    "-T",
    multiple=True,
    type=int,
    help="Task IDs to remove from the note (can be specified multiple times)",
)
def tag(
    note_id: int,
    add_contact: tuple,
    remove_contact: tuple,
    add_organization: tuple,
    remove_organization: tuple,
    add_task: tuple,
    remove_task: tuple,
):
    """Add or remove contact, organization, and task tags from a note."""
    if (
        not add_contact
        and not remove_contact
        and not add_organization
        and not remove_organization
        and not add_task
        and not remove_task
    ):
        click.echo(
            "❌ Please specify contacts, organizations, or tasks to add or remove",
            err=True,
        )
        return

    changes, error = NoteService.tag_note(
        note_id,
        add_contact_ids=list(add_contact) if add_contact else None,
        remove_contact_ids=list(remove_contact) if remove_contact else None,
        add_org_ids=list(add_organization) if add_organization else None,
        remove_org_ids=list(remove_organization) if remove_organization else None,
        add_task_ids=list(add_task) if add_task else None,
        remove_task_ids=list(remove_task) if remove_task else None,
    )

    if error:
        click.echo(f"❌ {error}", err=True)
        return

    if changes["added_contacts"]:
        click.echo(f"✅ Added contacts: {', '.join(changes['added_contacts'])}")
    if changes["removed_contacts"]:
        click.echo(f"✅ Removed contacts: {', '.join(changes['removed_contacts'])}")
    if changes["added_organizations"]:
        click.echo(
            f"✅ Added organizations: {', '.join(changes['added_organizations'])}"
        )
    if changes["removed_organizations"]:
        click.echo(
            f"✅ Removed organizations: {', '.join(changes['removed_organizations'])}"
        )
    if changes["added_tasks"]:
        click.echo(f"✅ Added tasks: {', '.join(changes['added_tasks'])}")
    if changes["removed_tasks"]:
        click.echo(f"✅ Removed tasks: {', '.join(changes['removed_tasks'])}")

    if not any(changes.values()):
        click.echo("ℹ️  No changes made")


if __name__ == "__main__":
    notes()
