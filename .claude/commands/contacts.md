---
description: Explain the contacts and notes CLI commands and demonstrate usage
---

You are helping the user manage contacts, notes, organizations and tasks using the CLI system located in `/home/seb/sites/alive-cli/commands/`.

## Available Commands

### Contact Management (`python main.py contacts`)

**Add a contact:**
```bash
python main.py contacts add -f <first_name> -l <last_name>
```

**List all contacts:**
```bash
python main.py contacts list
```

**Show top contacts by note count:**
```bash
python main.py contacts top [-n <limit>]
```

### Organization Management (`python main.py organizations`)

**Add an organization:**
```bash
python main.py organizations add -n <name>
```

**List all organizations:**
```bash
python main.py organizations list
```

**Show top organizations by note count:**
```bash
python main.py organizations top [-n <limit>]
```

### Note Management (`python main.py notes`)

**Add a note (with optional contact and organization tags):**
```bash
python main.py notes add -t "Title" -c "Content" [-C <contact_id>] [-O <org_id>] [-T <task_id>]
```

**List notes:**
```bash
python main.py notes list [-n <limit>] [-c <contact_id>] [-o <org_id>]
```

**View note details:**
```bash
python main.py notes view <note_id>
```

**Add/remove contact, organization, and task tags:**
```bash
python main.py notes tag <note_id> -a <contact_id> -A <org_id> -t <task_id> -r <contact_id> -R <org_id> -T <task_id>
```

### Task Management (`python main.py tasks`)

**Add a task:**
```bash
python main.py tasks add -t "Title" -D "YYYY-MM-DDTHH:MM:SS" -i <importance> [-C <contact_id>] [-O <org_id>]
```

**List tasks:**
```bash
python main.py tasks list [-n <limit>] [-C <contact_id>] [-O <org_id>] [--show-completed]
```

**View urgent tasks (due within 7 days):**
```bash
python main.py tasks urgent [-d <days>] [-s <sort_by>]
```

**Complete/uncomplete a task:**
```bash
python main.py tasks complete <task_id>
python main.py tasks uncomplete <task_id>
```

**View task details:**
```bash
python main.py tasks view <task_id>
```

**Add/remove contact and organization tags:**
```bash
python main.py tasks tag <task_id> -a <contact_id> -A <org_id> -r <contact_id> -R <org_id>
```

## CRITICAL RULES - ALWAYS FOLLOW

**ALWAYS tag notes with both contacts AND organizations when creating or discussing notes:**

1. **Before adding a note**: Check if the contacts and organizations exist. If not, create them first.
2. **When adding a note**: ALWAYS use `-C` flags for contacts and `-O` flags for organizations
3. **After creating a note without tags**: Immediately use `notes tag` to add missing contact/organization tags
4. **Never skip tagging**: Every business note should have at least one organization tag, and most should have contact tags

**Workflow for new notes:**
1. Create any missing contacts: `contacts add -f <name> -l <lastname>`
2. Create any missing organizations: `organizations add -n <org_name>`
3. Create any missing tasks: `tasks add -n <org_name>`
4. Add the note with tags: `notes add -t "Title" -c "Content" -C <contact_id> -O <org_id>`
5. If tags were missed, fix immediately: `notes tag <note_id> -a <contact_id> -A <org_id>`

## Your Task

1. **Start by running init**: `cd /home/seb/sites/alive-cli/commands && uv run python main.py init`
2. Show the user their latest 5 notes by running `cd /home/seb/sites/alive-cli/commands && uv run python main.py notes list -n 5`
3. Ask the user which note (if any) they would like to add a comment about or what new note they would like to create
4. **ALWAYS ensure all notes are properly tagged with contacts and organizations**

Be concise and helpful!
