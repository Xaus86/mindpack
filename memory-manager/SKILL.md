---
name: memory-manager
description: Manage persistent memory across sessions - add, replace, remove, and search memories. Also provides health reports, maintenance suggestions, and proactive memory capture. Triggers: remember this, I prefer, our project uses, the system is, memory status, memory health, how much memory do you have, clean up memory, deduplicate memory
allowed-tools: Read, write, Bash
---

# Memory Manager Skill

Manage persistent memory that persists across all sessions. Provides intelligent suggestions, proactive capture, and maintenance tools.

## Core Files

- **MEMORY.md**: `~/.openclaw/workspace/MEMORY.md` — Long-term memory (max ~2,200 chars)
- **USER.md**: `~/.openclaw/workspace/USER.md` — User profile and preferences (~1,375 chars)
- **Maintenance Script**: `~/.openclaw/workspace/skills/memory-manager/scripts/memory_maintenance.py`

## The Frozen Snapshot Pattern

Memory files are **snapshotted at session start** for stable prefix caching.
- New memories are written to disk immediately (durable)
- But the system prompt only refreshes at the **next session**
- This keeps your context window stable throughout each session

## Core Actions

### Reading Memory

```bash
# View current memory status (quick)
head -20 ~/.openclaw/workspace/MEMORY.md

# Full memory check
cat ~/.openclaw/workspace/MEMORY.md
cat ~/.openclaw/workspace/USER.md

# Memory health report
python3 ~/.openclaw/workspace/skills/memory-manager/scripts/memory_maintenance.py --report
```

### Adding a Memory

**When to add to MEMORY.md:**
- You learn a new fact about the environment
- You discover a project convention or tool quirk
- You learn something that saves the user from repeating themselves
- A decision or context is made that matters for future sessions

**When to add to USER.md:**
- User mentions a preference
- User corrects your behavior or approach
- User's workflow habits become clear
- User's goals or priorities shift

**Format:**
```
§ [Clear, factual statement]
```

Examples:
```
§ User prefers concise responses, dislikes verbose explanations
§ Project uses pytest with xdist for parallel test execution
§ Development server runs on port 3000
```

### Updating a Memory

1. Find the entry using a unique substring
2. Replace the old entry with the new version
3. Keep the `§` delimiter format

### Removing a Memory

1. Find the entry
2. Remove it entirely
3. Ensure no duplicate entries remain

## Proactive Memory Suggestions

**When to suggest memory capture:**

After these events, **proactively suggest** to the user:
- User mentions a preference, habit, or requirement → "Should I remember that?"
- You learn a new fact about their project/environment → "Want me to save this?"
- You discover something non-obvious that might be useful later → "This might be worth remembering"
- User corrects your approach → "I'll remember that for next time"

**The suggested format:**
```
💡 Should I remember "[concise fact statement]"?
→ Yes / No / Edit it first
```

## Memory Health Report

Run maintenance to check memory health:

```bash
python3 ~/.openclaw/workspace/skills/memory-manager/scripts/memory_maintenance.py --report
```

This checks for:
- **Duplicates**: Same fact recorded multiple times
- **Outdated entries**: Old dates, obsolete information
- **Long entries**: Entries over 400 chars that could be summarized
- **Usage**: How full each memory file is

## Memory Writing Rules

### Good Memory Entries ✓
```
§ User prefers concise responses, dislikes verbose explanations
§ Project uses pytest with xdist for parallel test execution
§ Development server runs on port 3000
§ API credentials are in ~/.env.local (never commit this file)
```

### Bad Memory Entries ✗
```
§ "User prefers concise responses" → Don't use imperative, it becomes a command
§ "Run tests with pytest -n 4" → Procedure, not fact. Put in a skill instead.
§ [Very long paragraph] → Brevity is key
```

### Key Distinction
- **Memory = Declarative facts** (what is)
- **Skill = Procedural knowledge** (how to do)

## Session Search vs Memory

| Session Search | Memory |
|---------------|--------|
| Finds past conversations | Stores current facts |
| Unlimited history | Bounded (~2k chars) |
| Raw transcript excerpts | Curated summaries |
| "What did we discuss about X?" | "I know that Y is true" |

Use **session_search** for finding past discussions.
Use **memory** for retaining learned facts.

## Security Note

Memory entries are injected into the system prompt.
**Never store:**
- API keys or secrets
- Passwords or credentials
- Private/personal information beyond what's needed
- Content from untrusted sources

## Memory Maintenance Cron

A cron job runs memory maintenance every 6 hours:
- Creates timestamped backups before any changes
- Generates a health report
- Alerts if maintenance is needed

Run manually:
```bash
python3 ~/.openclaw/workspace/skills/memory-manager/scripts/memory_maintenance.py
```