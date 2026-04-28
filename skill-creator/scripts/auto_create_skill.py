#!/usr/bin/env python3
"""
Auto-Skill Creator Tool
Helps AI automatically create skills from demonstrated workflows.

Usage (called by AI during conversation):
    python3 auto_create_skill.py --name <name> --description "<desc>" --body "<content>"
    python3 auto_create_skill.py --from-workflow --name <name> --description "<desc>" --steps "<steps>"

This script creates a SKILL.md file in the skills directory.
"""

import os
import re
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

SKILLS_DIR = Path.home() / ".openclaw" / "workspace" / "skills"
VALID_NAME_RE = re.compile(r'^[a-z][a-z0-9-]*$')
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024

def validate_name(name: str) -> tuple[bool, str]:
    """Validate skill name format."""
    if not name:
        return False, "Skill name is required."
    if len(name) > MAX_NAME_LENGTH:
        return False, f"Skill name exceeds {MAX_NAME_LENGTH} characters."
    if not VALID_NAME_RE.match(name):
        return False, (
            f"Invalid skill name '{name}'. Use lowercase letters, numbers, "
            f"hyphens, dots, and underscores. Must start with a letter or digit."
        )
    return True, ""

def validate_description(desc: str) -> tuple[bool, str]:
    """Validate skill description."""
    if not desc:
        return False, "Description is required."
    if len(desc) < 10:
        return False, "Description should be at least 10 characters."
    if len(desc) > MAX_DESCRIPTION_LENGTH:
        return False, f"Description exceeds {MAX_DESCRIPTION_LENGTH} characters."
    return True, ""

def create_skill_directory(name: str) -> tuple[Path, bool]:
    """Create skill directory. Returns (path, created_new)."""
    skill_dir = SKILLS_DIR / name
    
    if skill_dir.exists():
        return skill_dir, False
    
    skill_dir.mkdir(parents=True, exist_ok=True)
    return skill_dir, True

def generate_skill_content(name: str, description: str, body: str, allowed_tools: list = None) -> str:
    """Generate SKILL.md content from components."""
    if allowed_tools is None:
        allowed_tools = ["Read", "write", "exec", "Bash"]
    
    tools_str = ", ".join(allowed_tools)
    
    content = f"""---
name: {name}
description: "{description}"
allowed-tools: {tools_str}
---

# {name.replace('-', ' ').title().replace(' ', ' / ')}

## Overview

{description}

## The Process

{body}

## Tips

- Follow the steps precisely
- If something doesn't work, check the prerequisites first
- Update this skill if you find a better approach
"""

    return content

def create_skill(name: str, description: str, body: str, steps: list = None, allowed_tools: list = None, category: str = None) -> dict:
    """Create a new skill."""
    # Validate name
    valid, err = validate_name(name)
    if not valid:
        return {"success": False, "error": err}
    
    # Validate description
    valid, err = validate_description(description)
    if not valid:
        return {"success": False, "error": err}
    
    if not body and not steps:
        return {"success": False, "error": "Either body or steps are required"}
    
    # Create directory
    skill_dir, is_new = create_skill_directory(name)
    
    if not is_new:
        return {"success": False, "error": f"Skill '{name}' already exists at {skill_dir}"}
    
    # Generate body from steps if provided
    if steps and not body:
        body_lines = []
        for i, step in enumerate(steps, 1):
            body_lines.append(f"### Step {i}")
            body_lines.append(step)
            body_lines.append("")
        body = "\n".join(body_lines)
    
    # Generate content
    content = generate_skill_content(name, description, body, allowed_tools)
    
    # Write SKILL.md
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(content, encoding='utf-8')
    
    # Create subdirectories
    for subdir in ["references", "scripts", "templates", "assets"]:
        (skill_dir / subdir).mkdir(exist_ok=True)
    
    result = {
        "success": True,
        "message": f"Skill '{name}' created.",
        "path": str(skill_dir.relative_to(SKILLS_DIR)),
        "skill_md": str(skill_md),
        "skill_dir": str(skill_dir),
    }
    
    if category:
        result["category"] = category
    
    result["hint"] = (
        f"To add reference files, templates, or scripts, use the write tool to add to:\n"
        f"  {skill_dir}/references/\n"
        f"  {skill_dir}/scripts/\n"
        f"  {skill_dir}/templates/"
    )
    
    return result

def interactive_create() -> dict:
    """Interactive skill creation from user input."""
    print("Creating a new skill...")
    print()
    
    name = input("Skill name (lowercase, hyphenated): ").strip()
    valid, err = validate_name(name)
    if not valid:
        return {"success": False, "error": f"Name: {err}"}
    
    description = input("Description: ").strip()
    valid, err = validate_description(description)
    if not valid:
        return {"success": False, "error": f"Description: {err}"}
    
    print("Enter the skill body (end with empty line):")
    lines = []
    while True:
        line = input()
        if not line and lines:
            break
        lines.append(line)
    
    body = "\n".join(lines)
    
    return create_skill(name, description, body)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Auto-Skill Creator")
    parser.add_argument("--name", type=str, help="Skill name")
    parser.add_argument("--description", type=str, help="Skill description")
    parser.add_argument("--body", type=str, help="Skill body content (markdown)")
    parser.add_argument("--steps", nargs="+", help="Steps as separate arguments")
    parser.add_argument("--tools", nargs="+", help="Allowed tools list")
    parser.add_argument("--category", type=str, help="Optional category")
    
    args = parser.parse_args()
    
    if not args.name:
        # Interactive mode
        result = interactive_create()
        print(json.dumps(result, indent=2))
        return
    
    if not args.description:
        print("Error: --description is required", file=sys.stderr)
        sys.exit(1)
    
    result = create_skill(
        name=args.name,
        description=args.description,
        body=args.body or "",
        steps=args.steps,
        allowed_tools=args.tools,
        category=args.category
    )
    
    print(json.dumps(result, indent=2))
    
    if result["success"]:
        print(f"\n✅ Skill created at: {result['skill_dir']}")
    else:
        print(f"\n❌ Error: {result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()