#!/usr/bin/env python3
"""
Session Search Script
Searches past conversation sessions using SQLite FTS5 and returns AI summaries.

Usage:
    python3 search_sessions.py "query"
    python3 search_sessions.py "query" --limit 5
    python3 search_sessions.py "query" --summarize  # Returns just summary
"""

import sqlite3
import sys
import os
import json
import re
from datetime import datetime
from pathlib import Path

# Config
SESSIONS_DB = Path.home() / ".openclaw" / "workspace" / "state" / "sessions.db"
SESSIONS_DIR = Path.home() / ".openclaw" / "workspace" / "state"
MAX_SESSION_CHARS = 80000
MAX_SUMMARY_TOKENS = 4000

def get_recent_sessions(limit: int = 50) -> list:
    """Get the most recent sessions."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    sessions = []
    
    if SESSIONS_DB.exists():
        conn = sqlite3.connect(SESSIONS_DB)
        cursor = conn.execute("""
            SELECT session_id, updated_at, title 
            FROM sessions 
            ORDER BY updated_at DESC 
            LIMIT ?
        """, (limit,))
        sessions = cursor.fetchall()
        conn.close()
    
    # Fallback: scan state files
    if not sessions:
        state_dir = SESSIONS_DIR / "sessions"
        if state_dir.exists():
            for f in sorted(state_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:limit]:
                try:
                    data = json.loads(f.read_text())
                    sessions.append((
                        data.get("session_id", f.stem),
                        data.get("updated_at", f.stat().st_mtime),
                        data.get("title", "Untitled")
                    ))
                except:
                    pass
    
    return sessions

def search_sessions(query: str, limit: int = 5) -> list:
    """Search sessions for matching content."""
    results = []
    query_lower = query.lower()
    
    # Try FTS5 search first
    if SESSIONS_DB.exists():
        try:
            conn = sqlite3.connect(SESSIONS_DB)
            # Escape the query for FTS5 and add quotes for phrase search
            fts_query = f'"{query}"' if ' ' in query else query
            cursor = conn.execute(f"""
                SELECT messages_fts.session_id, snippet(messages_fts, 2, '【', '】', '...', 30) as snippet,
                       s.updated_at, s.title
                FROM messages_fts
                JOIN sessions s ON messages_fts.session_id = s.session_id
                WHERE messages_fts MATCH :query
                ORDER BY rank
                LIMIT :limit
            """, {"query": fts_query, "limit": limit})
            fts_results = cursor.fetchall()
            conn.close()
            
            for row in fts_results:
                results.append({
                    "session_id": row[0],
                    "snippet": row[1],
                    "updated_at": row[2],
                    "title": row[3],
                    "match_type": "fts"
                })
        except sqlite3.OperationalError as e:
            print(f"FTS error: {e}", file=sys.stderr)
            pass  # FTS table doesn't exist, fall through
    
    # Fallback: text search in session files
    if not results:
        results = text_search_sessions(query_lower, limit)
    
    return results

def text_search_sessions(query: str, limit: int = 5) -> list:
    """Fallback text search through session JSON files."""
    results = []
    state_dir = SESSIONS_DIR / "sessions"
    
    if not state_dir.exists():
        return results
    
    query_terms = query.lower().split()
    
    for session_file in sorted(state_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            data = json.loads(session_file.read_text())
            messages = data.get("messages", [])
            session_id = data.get("session_id", session_file.stem)
            updated_at = data.get("updated_at", session_file.stat().st_mtime)
            title = data.get("title", "Untitled")
            
            # Search through messages
            for msg in messages:
                content = str(msg.get("content", "")).lower()
                role = msg.get("role", "")
                
                # Check if all query terms appear in content
                if all(term in content for term in query_terms):
                    # Extract snippet around matches
                    snippet = extract_snippet(content, query_terms)
                    results.append({
                        "session_id": session_id,
                        "snippet": snippet,
                        "updated_at": updated_at,
                        "title": title,
                        "match_type": "text"
                    })
                    break  # One match per session is enough
                    
        except (json.JSONDecodeError, KeyError):
            continue
    
    return results[:limit]

def extract_snippet(content: str, query_terms: list, context_chars: int = 200) -> str:
    """Extract a snippet of content around the first matching term."""
    content_lower = content.lower()
    
    # Find the first matching term
    first_pos = len(content)
    for term in query_terms:
        pos = content_lower.find(term)
        if pos != -1 and pos < first_pos:
            first_pos = pos
    
    if first_pos == len(content):
        return content[:context_chars * 2] + "..."
    
    # Extract context around the match
    start = max(0, first_pos - context_chars)
    end = min(len(content), first_pos + context_chars)
    
    snippet = content[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(content):
        snippet = snippet + "..."
    
    return snippet

def format_timestamp(ts) -> str:
    """Format timestamp for display."""
    try:
        if isinstance(ts, (int, float)):
            dt = datetime.fromtimestamp(ts)
        else:
            dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return str(ts)[:19]

def format_results(results: list, query: str) -> str:
    """Format search results for display."""
    if not results:
        return f"No sessions found matching: \"{query}\""
    
    output = [f"Found {len(results)} relevant session(s):\n"]
    
    for i, r in enumerate(results, 1):
        title = r.get("title", "Untitled")
        ts = format_timestamp(r.get("updated_at", 0))
        snippet = r.get("snippet", "")
        match = r.get("match_type", "unknown")
        
        output.append(f"{'='*60}")
        output.append(f"[{i}] {title}")
        output.append(f"    📅 {ts} | Match: {match}")
        output.append(f"    💬 {snippet}")
        output.append("")
    
    output.append("="*60)
    output.append("💡 Tip: To dive deeper into a session, say 'show me session [id]'")
    
    return "\n".join(output)

def get_session_count() -> int:
    """Get total number of indexed sessions."""
    if SESSIONS_DB.exists():
        try:
            conn = sqlite3.connect(SESSIONS_DB)
            cursor = conn.execute("SELECT COUNT(*) FROM sessions")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except:
            pass
    
    # Fallback: count session files
    state_dir = SESSIONS_DIR / "sessions"
    if state_dir.exists():
        return len(list(state_dir.glob("*.json")))
    return 0

def main():
    if len(sys.argv) < 2:
        print("Usage: search_sessions.py <query> [--limit N]")
        sys.exit(1)
    
    query = sys.argv[1]
    limit = 5
    
    # Parse args
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            try:
                limit = int(sys.argv[idx + 1])
            except ValueError:
                pass
    
    session_count = get_session_count()
    print(f"🔍 Searching {session_count} sessions for: \"{query}\"\n")
    
    results = search_sessions(query, limit)
    print(format_results(results, query))

if __name__ == "__main__":
    main()
