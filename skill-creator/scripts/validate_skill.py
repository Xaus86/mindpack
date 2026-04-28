#!/usr/bin/env python3
"""
Validate Skill Script
Validates a skill's SKILL.md format and structure.

Usage:
    python3 validate_skill.py <skill-name>
    python3 validate_skill.py <skill-name> [--fix]
"""

import os
import re
import sys
from pathlib import Path

SKILLS_DIR = Path.home() / ".openclaw" / "workspace" / "skills"

REQUIRED_FRONTMATTER = ["name", "description"]
ALLOWED_TOOLS = [
    "Bash", "Read", "write", "Edit", "exec", "glob", "Grep", "web_fetch",
    "minimax-token-plan__web_search", "minimax-token-plan__understand_image",
    "image_generate", "video_generate", "music_generate", "cron"
]

def validate_name(name: str) -> tuple[bool, str]:
    """Validate skill name format."""
    if not re.match(r'^[a-z][a-z0-9-]*$', name):
        return False, "Name must start with lowercase letter and contain only lowercase letters, numbers, and hyphens"
    if len(name) > 64:
        return False, "Name must be 64 characters or less"
    return True, ""

def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from markdown."""
    if not content.startswith("---"):
        return {}, content
    
    end_match = re.search(r'\n---\s*\n', content[3:])
    if not end_match:
        return {}, content
    
    yaml_content = content[3:end_match.start() + 3]
    body = content[3 + end_match.end():]
    
    # Simple YAML parsing
    frontmatter = {}
    for line in yaml_content.strip().split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            frontmatter[key.strip()] = value.strip().strip('"').strip("'")
    
    return frontmatter, body

def validate_frontmatter(fm: dict) -> list[str]:
    """Validate frontmatter fields."""
    errors = []
    
    for field in REQUIRED_FRONTMATTER:
        if field not in fm:
            errors.append(f"Missing required frontmatter field: {field}")
    
    if 'description' in fm and len(fm['description']) < 10:
        errors.append("Description should be at least 10 characters")
    
    if 'allowed-tools' in fm:
        tools = [t.strip().split('(')[0] for t in fm['allowed-tools'].split(',')]
        for tool in tools:
            if tool and tool not in ALLOWED_TOOLS:
                errors.append(f"Unknown tool: {tool}")
    
    return errors

def validate_body(body: str) -> list[str]:
    """Validate skill body content."""
    errors = []
    
    if not body.strip():
        errors.append("SKILL.md body is empty")
        return errors
    
    # Check for basic structure
    lines = body.strip().split('\n')
    has_header = False
    has_content = len(body.strip()) > 100
    
    for line in lines:
        if line.startswith('# ') and not has_header:
            has_header = True
    
    if not has_header:
        errors.append("Missing H1 header (# Skill Name)")
    
    if not has_content:
        errors.append("Skill body seems too short (should have substantive content)")
    
    return errors

def main():
    if len(sys.argv) < 2:
        print("Usage: validate_skill.py <skill-name> [--fix]")
        sys.exit(1)
    
    skill_name = sys.argv[1]
    should_fix = "--fix" in sys.argv
    
    skill_path = SKILLS_DIR / skill_name / "SKILL.md"
    
    if not skill_path.exists():
        print(f"❌ Skill not found: {skill_path}")
        sys.exit(1)
    
    print(f"🔍 Validating skill: {skill_name}")
    
    # Read content
    content = skill_path.read_text()
    frontmatter, body = parse_frontmatter(content)
    
    all_errors = []
    
    # Validate
    name_valid, name_msg = validate_name(skill_name)
    if not name_valid:
        all_errors.append(name_msg)
    
    fm_errors = validate_frontmatter(frontmatter)
    all_errors.extend(fm_errors)
    
    body_errors = validate_body(body)
    all_errors.extend(body_errors)
    
    # Report
    if all_errors:
        print(f"\n❌ Found {len(all_errors)} issue(s):")
        for err in all_errors:
            print(f"   • {err}")
        print(f"\n📝 Skill location: {skill_path}")
        sys.exit(1)
    else:
        print(f"\n✅ Skill '{skill_name}' is valid!")
        print(f"   📍 {skill_path}")
        if frontmatter.get('description'):
            print(f"   📋 {frontmatter['description']}")
        sys.exit(0)

if __name__ == "__main__":
    main()
