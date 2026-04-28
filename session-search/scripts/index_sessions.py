#!/usr/bin/env python3
"""
Session Indexer
Indexes conversation sessions from OpenClaw's JSONL format into SQLite with FTS5.

OpenClaw stores sessions as JSONL files in:
  ~/.openclaw/agents/main/sessions/

Usage:
    python3 index_sessions.py          # Index all sessions
    python3 index_sessions.py --watch   # Watch for new sessions (daemon mode)
    python3 index_sessions.py --stats   # Show indexing statistics
"""

import sqlite3
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

# Config - OpenClaw session storage
AGENTS_SESSIONS_DIR = Path.home() / ".openclaw" / "agents" / "main" / "sessions"
STATE_DIR = Path.home() / ".openclaw" / "workspace" / "state"
SESSIONS_DB = STATE_DIR / "sessions.db"

def init_db():
    """Initialize the sessions database with FTS5 support."""
    SESSIONS_DB.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(SESSIONS_DB)
    
    # Sessions table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            title TEXT,
            updated_at INTEGER,
            created_at INTEGER,
            message_count INTEGER DEFAULT 0
        )
    """)
    
    # Messages table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            timestamp INTEGER,
            tool_calls TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)
    
    # FTS5 virtual table for full-text search
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
            session_id,
            role,
            content,
            content=messages,
            content_rowid=id
        )
    """)
    
    # Triggers to keep FTS in sync
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
            INSERT INTO messages_fts(rowid, session_id, role, content)
            VALUES (new.id, new.session_id, new.role, new.content);
        END
    """)
    
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
            INSERT INTO messages_fts(messages_fts, rowid, session_id, role, content)
            VALUES ('delete', old.id, old.session_id, old.role, old.content);
        END
    """)
    
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
            INSERT INTO messages_fts(messages_fts, rowid, session_id, role, content)
            VALUES ('delete', old.id, old.session_id, old.role, old.content);
            INSERT INTO messages_fts(rowid, session_id, role, content)
            VALUES (new.id, new.session_id, new.role, new.content);
        END
    """)
    
    conn.commit()
    conn.close()

def extract_text_content(content_array) -> str:
    """Extract text from OpenClaw's content array format."""
    if isinstance(content_array, str):
        return content_array
    
    if isinstance(content_array, list):
        parts = []
        for item in content_array:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(item.get("text", ""))
                elif item.get("type") == "tool_result":
                    parts.append(f"[Tool: {item.get('tool_name', 'unknown')}]: {item.get('content', '')}")
        return "\n".join(parts)
    
    return str(content_array) if content_array else ""

def parse_session_jsonl(filepath: Path) -> dict:
    """Parse a session JSONL file and extract all messages."""
    session_id = filepath.stem.replace(".reset", "").replace(".deleted", "")
    
    messages = []
    session_start = int(filepath.stat().st_ctime)
    session_updated = int(filepath.stat().st_mtime)
    title = "Untitled Session"
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                
                record_type = record.get("type")
                
                if record_type == "session":
                    # Get session metadata
                    if record.get("timestamp"):
                        try:
                            ts = datetime.fromisoformat(record["timestamp"].replace("Z", "+00:00"))
                            session_start = int(ts.timestamp())
                        except:
                            pass
                
                elif record_type == "message":
                    msg = record.get("message", {})
                    role = msg.get("role", "unknown")
                    content = extract_text_content(msg.get("content", ""))
                    
                    if content:
                        messages.append({
                            "role": role,
                            "content": content,
                            "timestamp": record.get("timestamp", "")
                        })
                
                elif record_type == "custom":
                    # Could contain session title
                    if record.get("key") == "title" or "title" in record.get("data", {}):
                        title = record.get("data", {}).get("title", title)
    
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return None
    
    # Generate title from first user message if not set
    if title == "Untitled Session":
        for msg in messages:
            if msg["role"] == "user":
                content = msg["content"][:80].replace("\n", " ")
                title = content + ("..." if len(msg["content"]) > 80 else "")
                break
    
    return {
        "session_id": session_id,
        "title": title,
        "updated_at": session_updated,
        "created_at": session_start,
        "messages": messages
    }

def index_session(session_data: dict) -> int:
    """Index a single session into the database."""
    conn = sqlite3.connect(SESSIONS_DB)
    cursor = conn.cursor()
    
    indexed_count = 0
    
    # Upsert session
    cursor.execute("""
        INSERT OR REPLACE INTO sessions (session_id, title, updated_at, created_at, message_count)
        VALUES (?, ?, ?, ?, ?)
    """, (
        session_data["session_id"],
        session_data.get("title", "Untitled"),
        session_data["updated_at"],
        session_data["created_at"],
        len(session_data["messages"])
    ))
    
    # Delete existing messages for this session (for re-indexing)
    cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_data["session_id"],))
    
    # Insert messages
    for msg in session_data["messages"]:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        
        if not content:
            continue
        
        cursor.execute("""
            INSERT INTO messages (session_id, role, content, timestamp, tool_calls)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session_data["session_id"],
            role,
            content[:50000],  # Truncate very long content
            int(time.time()),
            None
        ))
        indexed_count += 1
    
    conn.commit()
    conn.close()
    
    return indexed_count

def get_all_jsonl_files() -> list:
    """Find all session JSONL files."""
    if not AGENTS_SESSIONS_DIR.exists():
        return []
    
    files = []
    for f in AGENTS_SESSIONS_DIR.glob("*.jsonl"):
        # Skip deleted/reset files
        if ".deleted" in f.name or ".reset" in f.name:
            continue
        files.append(f)
    
    # Also include active sessions directory
    return sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)

def index_all_sessions() -> tuple[int, int]:
    """Index all session files found."""
    init_db()
    
    total_sessions = 0
    total_messages = 0
    
    files = get_all_jsonl_files()
    
    for filepath in files:
        session_data = parse_session_jsonl(filepath)
        if session_data and session_data["messages"]:
            count = index_session(session_data)
            total_sessions += 1
            total_messages += count
    
    return total_sessions, total_messages

def get_stats() -> dict:
    """Get indexing statistics."""
    if not SESSIONS_DB.exists():
        return {"sessions": 0, "messages": 0, "db_size_mb": 0}
    
    conn = sqlite3.connect(SESSIONS_DB)
    
    cursor = conn.execute("SELECT COUNT(*) FROM sessions")
    sessions = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM messages")
    messages = cursor.fetchone()[0]
    
    conn.close()
    
    db_size = SESSIONS_DB.stat().st_size / (1024 * 1024) if SESSIONS_DB.exists() else 0
    
    return {
        "sessions": sessions,
        "messages": messages,
        "db_size_mb": round(db_size, 2)
    }

def watch_mode(interval: int = 60):
    """Watch for new sessions and index them."""
    print(f"👀 Watch mode: checking every {interval}s. Press Ctrl+C to stop.")
    print(f"📁 Watching: {AGENTS_SESSIONS_DIR}")
    
    known_files = {f.name for f in get_all_jsonl_files()}
    
    while True:
        try:
            current_files = {f.name for f in get_all_jsonl_files()}
            new_files = current_files - known_files
            
            if new_files:
                for fname in new_files:
                    filepath = AGENTS_SESSIONS_DIR / fname
                    session_data = parse_session_jsonl(filepath)
                    if session_data and session_data["messages"]:
                        count = index_session(session_data)
                        print(f"📚 New session indexed: {session_data['title'][:50]}... ({count} messages)")
                
                known_files = current_files
            
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\n👋 Stopping watcher.")
            break

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Session Search Indexer")
    parser.add_argument("--watch", action="store_true", help="Watch mode for new sessions")
    parser.add_argument("--interval", type=int, default=60, help="Watch interval in seconds")
    parser.add_argument("--stats", action="store_true", help="Show indexing statistics")
    
    args = parser.parse_args()
    
    if args.watch:
        watch_mode(args.interval)
    elif args.stats:
        stats = get_stats()
        print(f"📊 Index Statistics:")
        print(f"   Sessions: {stats['sessions']}")
        print(f"   Messages: {stats['messages']}")
        print(f"   DB Size: {stats['db_size_mb']} MB")
        print(f"   DB Path: {SESSIONS_DB}")
        print(f"   Source: {AGENTS_SESSIONS_DIR}")
    else:
        print("📚 Indexing all sessions...")
        print(f"   Source: {AGENTS_SESSIONS_DIR}")
        sessions, messages = index_all_sessions()
        stats = get_stats()
        print(f"\n✅ Done! Indexed {sessions} sessions ({messages} messages)")
        print(f"   Total in DB: {stats['sessions']} sessions, {stats['messages']} messages")
        print(f"   DB size: {stats['db_size_mb']} MB")
        print(f"\n💡 To search sessions, use the session-search skill!")

if __name__ == "__main__":
    main()
