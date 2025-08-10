# CCNotify

[![Latest Release](https://img.shields.io/github/v/release/Helmi/CCNotify)](https://github.com/Helmi/CCNotify/releases/latest)
[![PyPI](https://img.shields.io/pypi/v/ccnotify)](https://pypi.org/project/ccnotify/)

## Voice Notification System for Claude Code

- 🗣️ Have your favourite Voide tell you what's up in Claude Code
- ⁉ Get notified when your Input is needed
- ⚠ Be aware of critical commands being executed
- 🏃‍♂️ Stay in control of multiple agents
- 🕵🏻‍♂️ Select between local TTS (Kokoro) and Elevenlabs (more to come)
- 💡 Sound caching system to save on API Credity/Processing time

**NOTE:** This is an early stage project I primarily designed around my own use cases.

❤️ Your input through Github Issues is highly appreciated.

## Platforms

Currently CCNotify is only tested on MacOS (15.5). Help testing or implementing other Platforms. PRs welcome.

## Quick Start

Interactive installer - guides you through everything. All you need is Python and UV installed.

```bash
uvx ccnotify install
```

That's it! The installer will:

- Help you choose between local (Kokoro) or cloud (ElevenLabs) TTS
- Download models if needed
- Install hooks into Claude Code
- Create a configuration file
- Guide you through next steps

Restart Claude Code to enable notifications.

**Troubleshooting:** Use `uvx ccnotify install --force` to completely reinstall if you encounter issues.

### Logging

By default, CCNotify runs without logging to prevent log files from growing too large. If you need to debug issues or track activity, you can enable logging:

```bash
# Install with logging enabled
uvx ccnotify install --logging

# Update existing installation to enable logging
uvx ccnotify install --logging

# Update existing installation to disable logging (default)
uvx ccnotify install
```

When logging is enabled, log files will be created in `~/.claude/ccnotify/logs/` with daily rotation.

## Support the work

If you want to support the project or me in Person, feel free to become a Github Sponsor.

If you use Elevenlabs as a TTS provider, [use my Affiliate link to signup](https://try.elevenlabs.io/ist8m7h95ed2).

## Features

- **Smart Filtering**: Only notifies for significant events, not routine operations
- **Dual TTS Options**: Local Kokoro models (50+ voices) or ElevenLabs cloud API
- **Project Detection**: Automatically identifies your current project
- **Zero Config**: Works out of the box with sensible defaults
- **Privacy First**: Local processing with optional cloud TTS


## Configuration

The installer creates a configuration file at `~/.claude/ccnotify/config.json`. Key settings:

**For Local TTS (Kokoro):**

```json
{
  "tts_provider": "kokoro",
  "voice": "af_heart",
  "speed": 1.0,
  "format": "mp3",
  "mp3_bitrate": "128k",
  "models_dir": "~/.claude/ccnotify/models"
}
```

> **Note:** `af_heart` is recommended as it provides the highest quality English pronunciation among Kokoro voices.

**For Cloud TTS (ElevenLabs):**

```json
{
  "tts_provider": "elevenlabs",
  "api_key": "your_api_key_here",
  "voice_id": "21m00Tcm4TlvDq8ikWAM",
  "model_id": "eleven_flash_v2_5"
}
```

**Voice Options:**

- **Kokoro**: `af_heart` (recommended), `af_sarah`, `am_adam`, `bf_alice`, `bm_daniel` and [40+ others](https://github.com/thewh1teagle/kokoro-onnx)
- **ElevenLabs**: Use voice IDs from your [ElevenLabs account](https://try.elevenlabs.io/ist8m7h95ed2)

**Pronunciation Customization:**

Customize how project names and commands are pronounced by editing `~/.claude/ccnotify/replacements.json`. CCNotify automatically discovers your projects and you can adjust their pronunciation:

```json
{
  "projects": {
    "ccnotify": {
      "folder": "-Users-helmi-code-ccnotify",
      "display_name": "CCNotify",
      "pronunciation": "CC notify"
    },
    "agent-zero": {
      "folder": "-Users-helmi-code-agent-zero",
      "display_name": "Agent Zero",
      "pronunciation": "agent zero"
    }
  },
  "commands": {
    "ls": "list",
    "cd": "change directory",
    "rm": "remove",
    "mkdir": "make directory",
    "npm": "N P M",
    "uvx": "U V X"
  },
  "patterns": [
    {
      "pattern": "npm run (\\w+)",
      "replacement": "N P M run {1}"
    },
    {
      "pattern": "git (push|pull|commit)",
      "replacement": "git {1}"
    },
    {
      "pattern": "(.+)\\.py",
      "replacement": "{1} python file"
    }
  ]
}
```

**Note:** Existing configurations will be automatically migrated to the new format on first load.

## Requirements

- macOS or Linux
- Python 3.10+
- Claude Code CLI
- **For Kokoro**: ~350MB disk space for local models
- **For ElevenLabs**: API account and internet connection

## Early Version Notice

This is an early release focused on core functionality. Features may change based on feedback.

**Issues & Suggestions**: Please use [GitHub Issues](https://github.com/Helmi/CCNotify/issues) to report problems or suggest improvements.

## How It Works

CCNotify hooks into Claude Code's tool execution events and provides audio notifications for:

- Potentially risky operations (file deletions, system commands)
- Task completion
- Error conditions
- Input requirements

The system filters out routine operations to avoid notification fatigue while keeping you informed of important events during long-running AI sessions.

## License

MIT
