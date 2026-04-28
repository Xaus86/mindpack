---
name: skill-creator
description: Create new skills for OpenClaw based on demonstrated expertise or recurring workflows. Also provides automated skill improvement and quality maintenance. Triggers: make this a skill, create a skill, save this workflow, turn this into a skill, remember how to, skill for this task, can you create a skill, automate this as a skill
allowed-tools: Read, write, Bash
---

# Skill Creator Skill

Transform demonstrated expertise into reusable skills that make future sessions smarter.

## Core Concept

Skills are your **procedural memory** — they capture *how* to do things, not just *what* you know. When you discover a valuable workflow, save it as a skill so you can reuse it next time.

## When to Trigger Skill Creation

**Proactively suggest creating a skill when:**

1. You complete a **complex task (5+ tool calls)** in a way that could generalize
2. You discover a **non-obvious workflow** that saves time
3. You fix an error using a **specific sequence of steps** that could help others
4. User explicitly asks to "make this a skill" or "save this as a skill"
5. You notice a **recurring pattern** that could be automated

**Example trigger scenarios:**
- "Every time we deploy, we do X, Y, Z" → Could become a `deploy-workflow` skill
- "For this client's reports, we always follow this format" → `client-report-format` skill
- "The way we debug this type of issue is..." → `debug-[type]` skill

## Skill Creation Workflow

### Step 1: Identify the Skill

Ask yourself:
- What's the **general problem** this solves? (not the specific instance)
- What's the **input** it expects?
- What's the **output** it produces?
- What **steps** are needed?

### Step 2: Draft the SKILL.md

Create a file at:
```
~/.openclaw/workspace/skills/<skill-name>/SKILL.md
```

### Step 3: Create Directory Structure

```bash
mkdir -p ~/.openclaw/workspace/skills/<skill-name>
mkdir -p ~/.openclaw/workspace/skills/<skill-name>/references
mkdir -p ~/.openclaw/workspace/skills/<skill-name>/scripts
mkdir -p ~/.openclaw/workspace/skills/<skill-name>/templates
```

### Step 4: Validate the Skill

```bash
python3 ~/.openclaw/workspace/skills/skill-creator/scripts/validate_skill.py <skill-name>
```

### Step 5: Report to User

Tell the user:
- Skill name and location
- What it does
- When it will be automatically suggested

## SKILL.md Format

```markdown
---
name: my-skill-name
description: "What this skill does. Start with an action verb. Be specific about when to use it."
allowed-tools: ToolName(tool-arg *) Read write exec
---

# My Skill Title

## Overview
Brief description of what this skill does and when to use it.

## Prerequisites
Any tools, files, or setup required.

## The Process

### Step 1: [Action]
Description of first step.

### Step 2: [Action]
Description of second step.

## Examples

### Example 1: [Scenario]
```
[Example commands/inputs]
```

## Tips
- Practical tips for this skill
- Common pitfalls to avoid
```

## Skill Quality Guidelines

**Good skill names:**
- `github-pr-review` ✅
- `deploy-rust-binary` ✅
- `analyze-log-errors` ✅
- `stuff` ❌

**Bad skill names:**
- `my-skill` ❌
- `useful` ❌
- `help` ❌

**Good descriptions:**
- "Review a GitHub PR, focusing on security issues and logic bugs" ✅
- "Parse and summarize error logs from application crash dumps" ✅

**Bad descriptions:**
- "Does things" ❌
- "Helps with tasks" ❌

## Auto-Skill Creation (AI-to-AI)

When you (as AI) discover a reusable pattern during conversation:

1. **Announce**: "I can save this as a skill for future sessions. Create it?"
2. **If yes**: Follow the SKILL.md format above, create the skill file
3. **Validate**: Run validate_skill.py to ensure proper format
4. **Report**: Tell the user the skill is ready and when it will trigger

**Automated improvement**:
When you use a skill and find it outdated/wrong:
→ **Automatically patch it** with `skill_manage(action='patch')`
→ Don't wait to be asked

## Auto-Creation Trigger Example

```
User: "Every time we deploy to production we have to do X, Y, Z steps manually"

AI: "This looks like a reusable workflow. Want me to create a 'production-deploy' skill that automates this?"

User: "Yes"

AI: 
1. Creates ~/.openclaw/workspace/skills/production-deploy/SKILL.md
2. Writes the skill content
3. Validates with validate_skill.py
4. Reports: "✅ Created 'production-deploy' skill. Next time you need to deploy, just say 'use production-deploy skill' and it'll walk you through the workflow automatically."
```

## Skill Directory Structure

```
~/.openclaw/workspace/skills/
├── skill-name/
│   ├── SKILL.md          # Required - the skill definition
│   ├── references/       # Optional - reference documentation
│   ├── scripts/          # Optional - helper scripts
│   ├── templates/        # Optional - template files
│   └── assets/           # Optional - images, etc.
```

## Skill Validation

Use the validate script to ensure quality:

```bash
python3 ~/.openclaw/workspace/skills/skill-creator/scripts/validate_skill.py <skill-name>
```

This checks:
- Frontmatter has required fields (name, description)
- Name format is valid (lowercase, hyphenated)
- Description is substantive (10+ chars)
- allowed-tools references valid tools

## Integration with Memory

Skills capture **procedures**. MEMORY.md captures **facts**.

| Memory | Skill |
|--------|-------|
| User prefers concise responses | How to write a concise response |
| Project uses PostgreSQL | How to connect to PostgreSQL |
| API keys are in .env | How to deploy with env vars |

## Auto-Maintenance

Skills improve over time through use:
- When a skill fails or is outdated → automatically patch it
- When you discover a better approach → update the skill
- Keep skills focused and small (one skill = one problem domain)

## Troubleshooting Failed Skills

If a skill doesn't work:
1. Check if the skill file exists and is valid
2. Verify allowed-tools includes all required tools
3. Run validation script for specific errors
4. Report the issue to the user with fix suggestions