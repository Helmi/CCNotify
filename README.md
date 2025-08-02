# CCNotify

🔔 Intelligent notification system for Claude Code with audio feedback

Early-stage project providing smart notifications for Claude Code tool usage with local text-to-speech support.

## Quick Start

```bash
# Interactive installer - guides you through everything
uvx ccnotify install
```

That's it! The installer will:
- Help you choose between local (Kokoro) or cloud (ElevenLabs) TTS
- Download models if needed
- Install hooks into Claude Code
- Create a configuration file
- Guide you through next steps

Restart Claude Code to enable notifications.

## Features

- **Smart Filtering**: Only notifies for significant events, not routine operations
- **Dual TTS Options**: Local Kokoro models (50+ voices) or ElevenLabs cloud API
- **Project Detection**: Automatically identifies your current project
- **Zero Config**: Works out of the box with sensible defaults
- **Privacy First**: Local processing with optional cloud TTS

## Commands

```bash
# Interactive installer
uvx ccnotify install                     # Guided setup with TTS provider selection
uvx ccnotify install --force             # Overwrite existing installation
uvx ccnotify install --non-interactive   # Skip prompts (hooks only)

# Manual TTS management
uvx ccnotify setup --kokoro             # Download local TTS models (~350MB)
uvx ccnotify setup --update             # Check for model updates
uvx ccnotify setup --voices             # List available voices
uvx ccnotify setup --cleanup            # Remove downloaded models

# Configuration
uvx ccnotify config --show              # Show configuration paths
uvx ccnotify config --init              # Initialize configuration
```

## Configuration

The installer creates a configuration file at `~/.claude/ccnotify/config.json`. Key settings:

**For Local TTS (Kokoro):**
```json
{
  "tts": { "provider": "kokoro", "enabled": true },
  "kokoro": {
    "voice": "af_sarah",
    "speed": 1.0,
    "models_dir": "models"
  }
}
```

**For Cloud TTS (ElevenLabs):**
```json
{
  "tts": { "provider": "elevenlabs", "enabled": true },
  "elevenlabs": {
    "api_key": "your_api_key_here",
    "voice_id": "21m00Tcm4TlvDq8ikWAM",
    "model_id": "eleven_flash_v2_5"
  }
}
```

**Voice Options:**
- **Kokoro**: `af_sarah`, `am_adam`, `bf_alice`, `bm_daniel` and [40+ others](https://github.com/thewh1teagle/kokoro-onnx)
- **ElevenLabs**: Use voice IDs from your [ElevenLabs account](https://elevenlabs.io/speech-synthesis)

## Requirements

- macOS or Linux  
- Python 3.9+
- Claude Code CLI
- **For Kokoro**: ~350MB disk space for local models
- **For ElevenLabs**: API account and internet connection

## Early Version Notice

This is v0.1.0 - an early release focused on core functionality. Features may change based on feedback.

**Issues & Suggestions**: Please use [GitHub Issues](https://github.com/Helmi/ccnotify/issues) to report problems or suggest improvements.

## How It Works

CCNotify hooks into Claude Code's tool execution events and provides audio notifications for:

- Potentially risky operations (file deletions, system commands)
- Task completion  
- Error conditions
- Input requirements

The system filters out routine operations to avoid notification fatigue while keeping you informed of important events during long-running AI sessions.

## License

MIT