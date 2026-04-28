---
name: session-search
description: Search and recall past conversations from session history. Use when user asks about something from previous sessions, mentions "last time we talked about", or wants to find information from old conversations. Triggers: did we discuss, earlier you mentioned, last time, previous session, search history, recall past conversation, what did we talk about, find previous discussion
allowed-tools: Bash(session-search *) Read exec
---

# Session Search Skill

Search through all past conversation sessions to find relevant context.

## Core Concept

This skill maintains a searchable index of all conversation sessions. When you need to recall information from the past, use `session_search` to find it.

## When to Use

- User asks about something from a "previous session" or "last time"
- User says "earlier you mentioned..." or "didn't we talk about..."
- You want to verify if something was already discussed/decided
- User wants to continue from where a previous session left off

## The Process

### Step 1: Run Session Search

Use the `session_search` tool with the query:

```bash
~/.openclaw/workspace/skills/session-search/scripts/search_sessions.py "user query here"
```

### Step 2: Review Results

The script returns:
- List of relevant past sessions with timestamps
- Relevance scores
- Summaries of matching conversations

### Step 3: Present to User

If relevant sessions are found:
1. Summarize the key findings
2. Note the date/time of the conversation
3. Offer to dive deeper into any specific session

### Step 4: If No Results

If no sessions match:
- Tell the user nothing was found in their conversation history
- Suggest what they might be looking for instead

## Important Notes

- Sessions are stored locally in SQLite with FTS5 full-text search
- Only your direct conversations with the assistant are searched
- Group conversations are NOT included (privacy)
- Results are summarized using AI, not raw transcripts

## Storage Location

Session index: `~/.openclaw/workspace/state/sessions.db`
