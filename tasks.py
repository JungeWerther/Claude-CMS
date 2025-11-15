"""
Task management CLI commands.
"""

from datetime import datetime, timedelta

import click

from lib.database import init_db
from services.task_service import TaskService


@click.group()
def tasks():
    """Manage tasks with due dates and importance scores."""
    # Ensure database is initialized
    init_db()


@tasks.command()
@click.option("--title", "-t", required=True, help="Task title")
@click.option("--description", "-d", default="", help="Task description")
@click.option(
    "--due-date",
    "-D",
    required=True,
    help="Due date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
)
@click.option(
    "--importance",
    "-i",
    default=0,
    type=int,
    help="Importance score (0-10, default: 0)",
)
@click.option(
    "--contact",
    "-C",
    multiple=True,
    type=int,
    help="Contact ID to tag (can be used multiple times)",
)
@click.option(
    "--organization",
    "-O",
    multiple=True,
    type=int,
    help="Organization ID to tag (can be used multiple times)",
)
def add(title, description, due_date, importance, contact, organization):
    """Add a new task with due date and importance."""
    # Parse due date
    try:
        # Try parsing with time first
        try:
            due_dt = datetime.fromisoformat(due_date)
        except ValueError:
            # Try parsing date only, set time to end of day
            due_dt = datetime.strptime(due_date, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59
            )
    except ValueError:
        click.echo(
            f"❌ Invalid date format: {due_date}. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS",
            err=True,
        )
        return

    task, error = TaskService.add_task(
        title=title,
        due_date=due_dt,
        importance=importance,
        description=description if description else None,
        contact_ids=list(contact) if contact else None,
        organization_ids=list(organization) if organization else None,
    )

    if error:
        click.echo(f"❌ {error}", err=True)
        return

    click.echo(f"✅ Task added: '{title}' (ID: {task.id})")
    click.echo(f"   Due: {due_dt.strftime('%Y-%m-%d %H:%M')}")
    click.echo(f"   Importance: {importance}/10")

    assert task
    if task.contacts:
        contact_names = [f"{c.first_name} {c.last_name}".strip() for c in task.contacts]
        click.echo(f"   Contacts: {', '.join(contact_names)}")
    if task.organizations:
        org_names = [o.name for o in task.organizations]
        click.echo(f"   Organizations: {', '.join(org_names)}")


@tasks.command()
@click.option(
    "--limit",
    "-n",
    default=20,
    type=int,
    help="Number of tasks to display (default: 20)",
)
@click.option(
    "--show-completed",
    "-c",
    is_flag=True,
    help="Include completed tasks in the list",
)
@click.option("--contact", "-C", type=int, help="Filter by contact ID")
@click.option("--organization", "-O", type=int, help="Filter by organization ID")
def list(limit, show_completed, contact, organization):
    """List tasks."""
    all_tasks = TaskService.list_tasks(limit, show_completed, contact, organization)

    if not all_tasks:
        click.echo("No tasks found.")
        return

    status_text = "All" if show_completed else "Incomplete"
    click.echo(f"\n📋 {status_text} Tasks (showing {len(all_tasks)}):\n")
    click.echo(
        f"{'ID':<6} {'Title':<40} {'Due Date':<20} {'Imp':<4} {'C':<4} {'O':<4} {'✓':<3}"
    )
    click.echo("-" * 85)

    now = datetime.utcnow()
    for task in all_tasks:
        contact_count = len(task.contacts)
        org_count = len(task.organizations)

        # Format due date with urgency indicator
        due_str = task.due_date.strftime("%Y-%m-%d %H:%M")
        if task.due_date < now:
            due_str = f"🔴 {due_str}"
        elif task.due_date < now + timedelta(days=7):
            due_str = f"🟡 {due_str}"

        # Truncate title if too long
        title = task.title[:37] + "..." if len(task.title) > 40 else task.title

        completed_mark = "✓" if task.completed else ""

        click.echo(
            f"{task.id:<6} {title:<40} {due_str:<20} {task.importance:<4} "
            f"{contact_count:<4} {org_count:<4} {completed_mark:<3}"
        )


@tasks.command()
@click.argument("task_id", type=int)
def view(task_id):
    """View detailed information about a task."""
    task = TaskService.get_task(task_id)

    if not task:
        click.echo(f"❌ Task with ID {task_id} not found", err=True)
        return

    click.echo(f"\n📋 Task #{task.id}: {task.title}")
    click.echo("=" * 80)
    click.echo(f"Status: {'✅ Completed' if task.completed else '⏳ Incomplete'}")
    click.echo(f"Due Date: {task.due_date.strftime('%Y-%m-%d %H:%M:%S')}")
    click.echo(f"Importance: {task.importance}/10")
    click.echo(f"Created: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    click.echo(f"Updated: {task.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")

    if task.description:
        click.echo(f"\nDescription:\n{task.description}")

    if task.contacts:
        click.echo("\n👥 Tagged Contacts:")
        for contact in task.contacts:
            click.echo(
                f"  • {contact.first_name} {contact.last_name} (ID: {contact.id})"
            )

    if task.organizations:
        click.echo("\n🏢 Tagged Organizations:")
        for org in task.organizations:
            click.echo(f"  • {org.name} (ID: {org.id})")

    click.echo()


@tasks.command()
@click.option(
    "--days",
    "-d",
    default=7,
    type=int,
    help="Number of days from now to consider urgent (default: 7)",
)
@click.option(
    "--sort-by",
    "-s",
    type=click.Choice(["urgency", "importance"], case_sensitive=False),
    default="urgency",
    help="Sort by urgency (due date) or importance (default: urgency)",
)
def urgent(days, sort_by):
    """Show tasks due within a certain timeframe (default: 7 days)."""
    urgent_tasks = TaskService.get_urgent_tasks(days, sort_by)

    if not urgent_tasks:
        click.echo(f"✅ No urgent tasks due within {days} days!")
        return

    click.echo(f"\n⚠️  Urgent Tasks (due within {days} days, sorted by {sort_by}):\n")
    click.echo(f"{'ID':<6} {'Title':<40} {'Due Date':<20} {'Imp':<4} {'C':<4} {'O':<4}")
    click.echo("-" * 82)

    now = datetime.utcnow()
    for task in urgent_tasks:
        contact_count = len(task.contacts)
        org_count = len(task.organizations)

        # Format due date with urgency indicator
        due_str = task.due_date.strftime("%Y-%m-%d %H:%M")
        if task.due_date < now:
            due_str = f"🔴 {due_str} (OVERDUE)"
        elif task.due_date < now + timedelta(days=1):
            due_str = f"🔴 {due_str} (today)"
        elif task.due_date < now + timedelta(days=3):
            due_str = f"🟡 {due_str}"

        # Truncate title if too long
        title = task.title[:37] + "..." if len(task.title) > 40 else task.title

        click.echo(
            f"{task.id:<6} {title:<40} {due_str:<20} {task.importance:<4} "
            f"{contact_count:<4} {org_count:<4}"
        )


@tasks.command()
@click.argument("task_id", type=int)
def complete(task_id):
    """Mark a task as completed."""
    task, error = TaskService.complete_task(task_id)

    if error:
        click.echo(f"❌ {error}", err=True)
        return

    click.echo(f"✅ Task completed: '{task.title}' (ID: {task.id})")


@tasks.command()
@click.argument("task_id", type=int)
def uncomplete(task_id):
    """Mark a task as incomplete."""
    task, error = TaskService.uncomplete_task(task_id)

    if error:
        click.echo(f"❌ {error}", err=True)
        return

    click.echo(f"⏳ Task marked incomplete: '{task.title}' (ID: {task.id})")


@tasks.command()
@click.argument("task_id", type=int)
@click.option("--add-contact", "-a", multiple=True, type=int, help="Add contact ID")
@click.option(
    "--add-organization", "-A", multiple=True, type=int, help="Add organization ID"
)
@click.option(
    "--remove-contact", "-r", multiple=True, type=int, help="Remove contact ID"
)
@click.option(
    "--remove-organization",
    "-R",
    multiple=True,
    type=int,
    help="Remove organization ID",
)
def tag(task_id, add_contact, add_organization, remove_contact, remove_organization):
    """Add or remove contact and organization tags from a task."""
    changes, error = TaskService.tag_task(
        task_id,
        add_contact_ids=list(add_contact) if add_contact else None,
        add_org_ids=list(add_organization) if add_organization else None,
        remove_contact_ids=list(remove_contact) if remove_contact else None,
        remove_org_ids=list(remove_organization) if remove_organization else None,
    )

    if error:
        click.echo(f"❌ {error}", err=True)
        return
    assert changes
    if changes["added_contacts"]:
        click.echo(f"✅ Added contacts: {', '.join(changes['added_contacts'])}")
    if changes["removed_contacts"]:
        click.echo(f"➖ Removed contacts: {', '.join(changes['removed_contacts'])}")
    if changes["added_organizations"]:
        click.echo(
            f"✅ Added organizations: {', '.join(changes['added_organizations'])}"
        )
    if changes["removed_organizations"]:
        click.echo(
            f"➖ Removed organizations: {', '.join(changes['removed_organizations'])}"
        )

    if not (
        changes["added_contacts"]
        or changes["removed_contacts"]
        or changes["added_organizations"]
        or changes["removed_organizations"]
    ):
        click.echo("ℹ️  No changes made")


if __name__ == "__main__":
    tasks()
