# CCNotify Project Structure

## Overview
CCNotify is a notification system for Claude Code that provides intelligent, context-aware notifications for tool usage and execution events. It includes audio feedback through text-to-speech and visual notifications on supported platforms.

## Directory Structure

```
ccnotify/
├── notify.py              # Main notification handler script
├── replacements.json     # Configuration for text replacements
├── .env.example          # Example environment configuration
├── README.md            # Project documentation
├── docs/                # Additional documentation
│   ├── PROJECT_STRUCTURE.md  # This file
│   └── SETUP.md         # Installation and setup guide
├── sounds/              # Pre-generated sound files (created on first run)
└── logs/                # Notification logs (optional, created when logging enabled)
```

## Core Components

### notify.py
The main notification handler that:
- Processes Claude Code hook events
- Determines notification importance (filters out routine operations)
- Resolves project context from session IDs
- Generates appropriate visual and audio notifications
- Supports multiple TTS providers (macOS say, ElevenLabs, etc.)



### replacements.json
Configuration file that allows customization of:
- Project name mappings (e.g., technical folder names to friendly names)
- Command descriptions for audio notifications
- Pattern-based replacements for complex commands

## Configuration Files

### .env
Environment variables for:
- `USE_TTS`: Enable/disable text-to-speech (default: false)
- `USE_LOGGING`: Enable/disable logging (default: false)
- `ELEVENLABS_API_KEY`: API key for ElevenLabs TTS
- `ELEVENLABS_VOICE_ID`: Voice selection for ElevenLabs
- `ELEVENLABS_MODEL_ID`: Model selection for ElevenLabs

### Claude Code Settings
To use CCNotify, you need to configure hooks in your Claude Code settings:
- `~/.claude/settings.json` or `~/.claude/settings.local.json`

## Generated Files

### sounds/
Directory containing cached TTS audio files:
- Pre-generated system sounds (*.aiff)
- Cached ElevenLabs responses (elevenlabs_*.mp3)
- Automatically created on first use

### logs/
Directory containing notification logs:
- Daily log files (notifications_YYYYMMDD.log)
- Only created when logging is enabled
- Useful for debugging and monitoring

### session_project_cache.json
Cache file that maps Claude Code session IDs to project names for faster lookups.