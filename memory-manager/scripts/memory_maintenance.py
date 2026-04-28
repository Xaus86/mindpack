#!/usr/bin/env python3
"""
Memory Maintenance Script
Performs automated memory hygiene: deduplication, summarization, expiry.

Run via cron: python3 memory_maintenance.py
Or manually: python3 memory_maintenance.py --report

This script does NOT modify memory files directly.
It generates a report of suggested actions for the AI to review and execute.
"""

import re
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

MEMORY_FILE = Path.home() / ".openclaw" / "workspace" / "MEMORY.md"
USER_FILE = Path.home() / ".openclaw" / "workspace" / "USER.md"
BACKUP_DIR = Path.home() / ".openclaw" / "workspace" / "memory" / "backups"

ENTRY_DELIMITER = "\n§\n"
MAX_MEMORY_CHARS = 2200
MAX_USER_CHARS = 1375

def load_entries(filepath: Path) -> List[str]:
    """Load memory entries from a file.
    
    Supports two formats:
    1. §-delimited format: entries separated by "§" on its own line
    2. Markdown header format: entries starting with "## " sections
    
    The § format takes precedence if both patterns are detected,
    to maintain backward compatibility with the intended design.
    """
    if not filepath.exists():
        return []
    
    content = filepath.read_text()
    if not content.strip():
        return []
    
    # Strategy: Detect which format is actually in use
    # If § appears as a standalone line delimiter, use §-splitting
    # Otherwise fall back to ## header splitting
    
    lines = content.split('\n')
    has_section_markers = any(line.strip() == '§' for line in lines)
    has_header_markers = any(line.startswith('## ') for line in lines)
    
    if has_section_markers:
        # Use § delimiter format
        entries = []
        for part in content.split('\n§\n'):
            part = part.strip()
            if part:
                entries.append(part)
        # If § is present but split produced nothing, try raw § split
        if not entries:
            for part in content.split('§'):
                part = part.strip()
                if part:
                    entries.append(part)
    elif has_header_markers:
        # Use ## header format (current MEMORY.md structure)
        entries = []
        current_lines = []
        in_header_section = False
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('## '):
                # Save previous section
                if current_lines:
                    section_text = '\n'.join(current_lines).strip()
                    if section_text:
                        entries.append(section_text)
                # Start new section
                current_lines = [line]
                in_header_section = True
            elif in_header_section:
                current_lines.append(line)
        
        # Don't forget the last section
        if current_lines:
            section_text = '\n'.join(current_lines).strip()
            if section_text:
                entries.append(section_text)
    else:
        # No clear structure, treat entire content as single entry
        entries = [content.strip()]
    
    # Filter out the title line (first # heading) from each entry
    # This keeps entries focused on content, not metadata
    cleaned_entries = []
    for entry in entries:
        lines = entry.split('\n')
        # Skip entries that are just a title with no real content
        if len(lines) == 1 and lines[0].startswith('#'):
            continue
        cleaned_entries.append(entry)
    
    return cleaned_entries

def find_duplicates(entries: List[str]) -> List[Tuple[int, int]]:
    """Find duplicate or near-duplicate entries. Returns list of (idx, duplicate_of_idx)."""
    duplicates = []
    seen = {}
    
    for i, entry in enumerate(entries):
        # Normalize for comparison (lowercase, remove extra whitespace)
        normalized = ' '.join(entry.lower().split())
        
        if normalized in seen:
            duplicates.append((i, seen[normalized]))
        else:
            # Check for near-duplicates (one is substring of other)
            for j, other in enumerate(entries):
                if i != j and i > j:
                    other_norm = ' '.join(other.lower().split())
                    # If one is subset of another (at least 80% overlap)
                    if len(normalized) > 20 and len(other_norm) > 20:
                        if normalized in other_norm or other_norm in normalized:
                            # Keep the longer, more detailed one
                            if len(entry) >= len(other):
                                duplicates.append((i, j))
                            else:
                                if j not in [dup[1] for dup in duplicates]:
                                    duplicates.append((j, i))
                            break
            seen[normalized] = i
    
    return duplicates

def find_outdated_entries(entries: List[str], max_age_days: int = 90) -> List[Tuple[int, str]]:
    """Find entries that appear to contain outdated information."""
    outdated = []
    date_patterns = [
        r'(20\d{2})[-/]\d{1,2}[-/]\d{1,2}',  # 2024-01-01
        r'，距[今昨]\s*\d+',  # 距今3天
        r'\d+天前',  # 3天前
        r'(去年|前年|今年早些?|早些时候)',  # outdated relative to current year
    ]
    
    cutoff = datetime.now() - timedelta(days=max_age_days)
    
    for i, entry in enumerate(entries):
        # Check for date mentions
        for pattern in date_patterns:
            matches = re.findall(pattern, entry)
            for match in matches:
                if match.isdigit() and len(match) == 4:
                    year = int(match)
                    if year < 2024:  # Consider pre-2024 as potentially outdated
                        outdated.append((i, f"Contains year {year}"))
                        break
                elif '去年' in entry or '前年' in entry:
                    outdated.append((i, "Contains outdated relative date"))
                    break
        
        # Check for very old entries (no date but content suggests obsolescence)
        if any(word in entry.lower() for word in ['已停用', '已废弃', '不再使用', '旧版', '过时']):
            outdated.append((i, "Contains obsolescence indicator"))
    
    return outdated

def summarize_long_entries(entries: List[str], max_chars: int = 200) -> List[Tuple[int, str]]:
    """Suggest summarization for entries that are too long."""
    suggestions = []
    
    for i, entry in enumerate(entries):
        if len(entry) > max_chars * 2:
            # Entry is very long, suggest summarization
            preview = entry[:100] + "..."
            suggestions.append((i, f"SUMMARY CANDIDATE ({len(entry)} chars): {preview}"))
    
    return suggestions

def calculate_usage(filepath: Path, entries: List[str], max_chars: int) -> Dict:
    """Calculate memory usage statistics."""
    total_chars = len(ENTRY_DELIMITER.join(entries)) if entries else 0
    
    return {
        "filepath": str(filepath),
        "entry_count": len(entries),
        "total_chars": total_chars,
        "max_chars": max_chars,
        "usage_pct": int((total_chars / max_chars) * 100) if max_chars > 0 else 0,
        "healthy": total_chars < max_chars * 0.9,
        "near_full": total_chars > max_chars * 0.8,
    }

def generate_deduplication_actions(duplicates: List[Tuple[int, int]]) -> List[str]:
    """Generate suggested actions for deduplication."""
    actions = []
    to_remove = set()
    
    for dup_idx, orig_idx in duplicates:
        if dup_idx in to_remove:
            continue
        
        # Always keep the first occurrence
        to_remove.add(dup_idx)
        actions.append(f"REMOVE entry #{dup_idx+1} (duplicate of entry #{orig_idx+1})")
    
    return actions

def generate_cleanup_report(memory_file: str, user_file: str) -> str:
    """Generate a complete maintenance report."""
    mem_entries = load_entries(Path(memory_file))
    user_entries = load_entries(Path(user_file))
    
    mem_usage = calculate_usage(Path(memory_file), mem_entries, MAX_MEMORY_CHARS)
    user_usage = calculate_usage(Path(user_file), user_entries, MAX_USER_CHARS)
    
    report = []
    report.append("=" * 60)
    report.append("📊 MEMORY MAINTENANCE REPORT")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append("=" * 60)
    
    # Usage stats
    report.append("\n📈 MEMORY.md Usage:")
    report.append(f"   Entries: {mem_usage['entry_count']}")
    report.append(f"   Characters: {mem_usage['total_chars']}/{mem_usage['max_chars']} ({mem_usage['usage_pct']}%)")
    report.append(f"   Status: {'✅ Healthy' if mem_usage['healthy'] else '⚠️ Near full' if mem_usage['near_full'] else '❌ Full'}")
    
    report.append("\n📈 USER.md Usage:")
    report.append(f"   Entries: {user_usage['entry_count']}")
    report.append(f"   Characters: {user_usage['total_chars']}/{user_usage['max_chars']} ({user_usage['usage_pct']}%)")
    report.append(f"   Status: {'✅ Healthy' if user_usage['healthy'] else '⚠️ Near full' if user_usage['near_full'] else '❌ Full'}")
    
    # Duplicates
    mem_dups = find_duplicates(mem_entries)
    user_dups = find_duplicates(user_entries)
    
    report.append("\n🔄 Duplicates:")
    if mem_dups:
        report.append(f"   MEMORY.md: {len(mem_dups)} duplicate(s) found")
        for dup, orig in mem_dups[:5]:
            report.append(f"   - Entry #{dup+1} (← {mem_entries[dup][:60]}...) duplicates Entry #{orig+1}")
    else:
        report.append("   MEMORY.md: ✅ No duplicates")
    
    if user_dups:
        report.append(f"   USER.md: {len(user_dups)} duplicate(s) found")
        for dup, orig in user_dups[:5]:
            report.append(f"   - Entry #{dup+1} (← {user_entries[dup][:60]}...) duplicates Entry #{orig+1}")
    else:
        report.append("   USER.md: ✅ No duplicates")
    
    # Outdated
    mem_outdated = find_outdated_entries(mem_entries)
    user_outdated = find_outdated_entries(user_entries)
    
    report.append("\n📅 Outdated Entries:")
    if mem_outdated:
        report.append(f"   MEMORY.md: {len(mem_outdated)} potentially outdated")
    else:
        report.append("   MEMORY.md: ✅ No outdated entries detected")
    
    if user_outdated:
        report.append(f"   USER.md: {len(user_outdated)} potentially outdated")
    else:
        report.append("   USER.md: ✅ No outdated entries detected")
    
    # Long entries
    mem_long = summarize_long_entries(mem_entries)
    user_long = summarize_long_entries(user_entries)
    
    report.append("\n📝 Long Entry Candidates:")
    if mem_long:
        report.append(f"   MEMORY.md: {len(mem_long)} entry/entries over {200*2} chars - consider summarizing")
    else:
        report.append("   MEMORY.md: ✅ All entries are reasonably sized")
    
    if user_long:
        report.append(f"   USER.md: {len(user_long)} entry/entries over {200*2} chars - consider summarizing")
    else:
        report.append("   USER.md: ✅ All entries are reasonably sized")
    
    # Action summary
    report.append("\n" + "=" * 60)
    report.append("📋 RECOMMENDED ACTIONS")
    report.append("=" * 60)
    
    total_actions = len(mem_dups) + len(user_dups) + len(mem_outdated) + len(user_outdated) + len(mem_long) + len(user_long)
    
    if total_actions == 0:
        report.append("\n✅ No maintenance actions needed. Memory is in good shape!")
    else:
        if mem_dups:
            report.append(f"\n[DEDUP] Remove {len(mem_dups)} duplicate(s) from MEMORY.md")
        if user_dups:
            report.append(f"[DEDUP] Remove {len(user_dups)} duplicate(s) from USER.md")
        if mem_outdated:
            report.append(f"[UPDATE] Review {len(mem_outdated)} outdated MEMORY.md entries")
        if user_outdated:
            report.append(f"[UPDATE] Review {len(user_outdated)} outdated USER.md entries")
        if mem_long:
            report.append(f"[SUMMARIZE] Consider summarizing {len(mem_long)} long MEMORY.md entries")
        if user_long:
            report.append(f"[SUMMARIZE] Consider summarizing {len(user_long)} long USER.md entries")
    
    report.append("\n" + "=" * 60)
    
    return "\n".join(report)

def create_backup():
    """Create a timestamped backup of current memory files.
    
    Uses shutil.copy2 to preserve the original file while creating a backup copy.
    The original file stays in place; only a copy goes to the backup directory.
    """
    import shutil
    
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for filepath in [MEMORY_FILE, USER_FILE]:
        if filepath.exists():
            backup_path = BACKUP_DIR / f"{filepath.stem}_{timestamp}{filepath.suffix}"
            shutil.copy2(filepath, backup_path)
            print(f"📦 Backed up: {filepath.name} → {backup_path.name}")

def main():
    if "--report" in sys.argv or "-r" in sys.argv:
        # Just generate report
        print(generate_cleanup_report(str(MEMORY_FILE), str(USER_FILE)))
    elif "--backup" in sys.argv or "-b" in sys.argv:
        # Create backup
        create_backup()
        print("✅ Backups created")
    else:
        # Full maintenance: backup + report
        create_backup()
        print()
        print(generate_cleanup_report(str(MEMORY_FILE), str(USER_FILE)))
        print("\n💡 Run with --report to see report without backup")

if __name__ == "__main__":
    main()