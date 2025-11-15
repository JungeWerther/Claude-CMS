"""
Main CLI entry point.
"""

from datetime import datetime, timedelta

import click
from sqlalchemy import func, select

from contacts import contacts
from lib.database import get_db_session, init_db
from models.contact_note import ContactDB, NoteDB
from models.task import TaskDB
from notes import notes
from organizations import organizations
from tasks import tasks


@click.group()
def cli():
    """Commands CLI - Contact, Organization, Note, and Task management."""
    pass


@cli.command()
def init():
    """Initialize context: show 7-day calendar, 5 urgent tasks, and top contacts."""
    init_db()

    with get_db_session() as session:
        now = datetime.utcnow()

        # Display 7-day calendar
        click.echo("\n" + "=" * 80)
        click.echo("📅 THIS WEEK")
        click.echo("=" * 80 + "\n")

        days = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        for i in range(7):
            date = now + timedelta(days=i)
            day_name = days[date.weekday()]
            date_str = date.strftime("%Y-%m-%d")

            # Check if this is today
            if i == 0:
                click.echo(f"  ► {day_name:<10} {date_str}  ← TODAY")
            else:
                click.echo(f"    {day_name:<10} {date_str}")

        # Display 5 most urgent tasks
        click.echo("\n" + "=" * 80)
        click.echo("⚠️  TOP 5 URGENT TASKS")
        click.echo("=" * 80 + "\n")

        threshold = now + timedelta(days=7)
        stmt = (
            select(TaskDB)
            .where(TaskDB.completed == 0, TaskDB.due_date <= threshold)
            .order_by(TaskDB.due_date.asc())
            .limit(5)
        )
        urgent_tasks = session.execute(stmt).scalars().all()

        if urgent_tasks:
            for task in urgent_tasks:
                session.refresh(task, ["contacts", "organizations"])

                # Format due date with urgency indicator
                due_str = task.due_date.strftime("%Y-%m-%d %H:%M")
                if task.due_date < now:
                    status = "🔴 OVERDUE"
                elif task.due_date < now + timedelta(days=1):
                    status = "🔴 TODAY"
                elif task.due_date < now + timedelta(days=3):
                    status = "🟡 SOON"
                else:
                    status = "🟢 THIS WEEK"

                click.echo(f"  {status:<15} [{task.importance}/10] {task.title}")
                click.echo(f"  {'':15} Due: {due_str}")

                # Show tagged contacts/orgs if any
                if task.contacts or task.organizations:
                    tags = []
                    if task.contacts:
                        tags.append(
                            f"👥 {', '.join([f'{c.first_name} {c.last_name}'.strip() for c in task.contacts])}"
                        )
                    if task.organizations:
                        tags.append(
                            f"🏢 {', '.join([o.name for o in task.organizations])}"
                        )
                    click.echo(f"  {'':15} {' | '.join(tags)}")

                click.echo()
        else:
            click.echo("  ✅ No urgent tasks!\n")

        # Display top 5 contacts with recent notes
        click.echo("=" * 80)
        click.echo("📊 TOP 5 CONTACTS BY NOTE COUNT")
        click.echo("=" * 80 + "\n")

        stmt = (
            select(ContactDB, func.count(NoteDB.id).label("note_count"))
            .outerjoin(ContactDB.notes)
            .group_by(ContactDB.id)
            .order_by(func.count(NoteDB.id).desc())
            .limit(5)
        )
        top_contacts = session.execute(stmt).all()

        if top_contacts:
            for contact, note_count in top_contacts:
                click.echo(
                    f"  👤 {contact.first_name} {contact.last_name} (ID: {contact.id}) - {note_count} note(s)"
                )

                # Get last 3 notes for this contact
                session.refresh(contact, ["notes"])
                last_notes = sorted(
                    contact.notes, key=lambda n: n.created_at, reverse=True
                )[:3]

                if last_notes:
                    for note in last_notes:
                        created = note.created_at.strftime("%Y-%m-%d")
                        preview = (
                            note.content[:60] + "..."
                            if len(note.content) > 60
                            else note.content
                        )
                        click.echo(f"     • [{created}] {note.title}")
                        click.echo(f"       {preview}")
                else:
                    click.echo("     (No notes)")
                click.echo()
        else:
            click.echo("  No contacts found.\n")

        click.echo("=" * 80 + "\n")


# Register command groups
cli.add_command(contacts)
cli.add_command(notes)
cli.add_command(organizations)
cli.add_command(tasks)


if __name__ == "__main__":
    cli()
