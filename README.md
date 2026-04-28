# 🧠 MindPack

> Memory + Skills for OpenClaw — Make your AI assistant smarter over time.

**MindPack** is a collection of skills for [OpenClaw](https://github.com/openclaw/openclaw) that add long-term memory, conversation search, and automatic skill creation capabilities.

## Features

### 📚 Session Search (`session-search`)
Search and recall past conversations from your entire chat history.

- Full-text search powered by SQLite FTS5
- AI-powered summarization of relevant sessions
- Automatic background indexing every 30 minutes
- Privacy-respecting: only searches your direct conversations

### ✨ Skill Creator (`skill-creator`)
Transform demonstrated expertise into reusable skills.

- Manual skill creation via skill creation workflow
- AI-assisted skill drafting
- Automatic skill validation
- Quality guidelines and best practices

### 💾 Memory Manager (`memory-manager`)
Intelligent long-term memory for your AI assistant.

- Proactive memory suggestions ("Should I remember that?")
- Automatic memory maintenance (deduplication, cleanup)
- Memory health reports
- Frozen snapshot pattern for stable context

## Installation

### Option 1: Install All Skills

```bash
# Copy skills to your OpenClaw skills directory
cp -r session-search ~/.openclaw/workspace/skills/
cp -r skill-creator ~/.openclaw/workspace/skills/
cp -r memory-manager ~/.openclaw/workspace/skills/
```

### Option 2: Install Individually

```bash
# Session Search (requires indexing script)
cp -r session-search ~/.openclaw/workspace/skills/

# Skill Creator
cp -r skill-creator ~/.openclaw/workspace/skills/

# Memory Manager
cp -r memory-manager ~/.openclaw/workspace/skills/
```

## Quick Start

After installation, the skills are automatically discovered by OpenClaw.

### Session Search
```
You: What did we discuss about Tailwind last time?
AI: [Uses session-search skill to find relevant past conversations]
```

### Create a Skill
```
You: Make this deployment process a skill
AI: [Uses skill-creator skill to create SKILL.md]
```

### Memory Management
```
You: I prefer concise responses
AI: Should I remember that? → Yes / No
```

## Requirements

- OpenClaw installed and configured
- Python 3.8+ (for scripts)
- SQLite with FTS5 support (built into Python)

## Project Structure

```
mindpack/
├── session-search/
│   ├── SKILL.md           # Skill definition
│   └── scripts/
│       ├── index_sessions.py    # Background indexer
│       └── search_sessions.py   # Search interface
├── skill-creator/
│   ├── SKILL.md           # Skill definition
│   └── scripts/
│       ├── validate_skill.py      # Quality validation
│       └── auto_create_skill.py   # AI skill creation
├── memory-manager/
│   ├── SKILL.md           # Skill definition
│   └── scripts/
│       └── memory_maintenance.py  # Health check & cleanup
└── README.md
```

## Skills Documentation

Each skill has its own `SKILL.md` with detailed usage instructions. OpenClaw will automatically include them when relevant.

## Compatibility

MindPack is designed to be compatible with future OpenClaw versions:
- Skills are pure SKILL.md format (no internal API dependencies)
- Scripts live in workspace (not in OpenClaw source)
- No modifications to OpenClaw core

## License

MIT License - feel free to use, modify, and distribute.

## Contributing

Contributions welcome! Areas for improvement:
- Additional memory providers
- More search backends
- Skill templates library

## Acknowledgments

Inspired by [Hermes Agent](https://github.com/NousResearch/hermes-agent) and its self-learning capabilities. MindPack brings similar concepts to OpenClaw users.
