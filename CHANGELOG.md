# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.5] - 2025-08-03

### 🐛 Fixed

- **Update flow now fixes detected issues**: The updater now actually fixes the issues it detects
  - Downloads missing Kokoro models when detected
  - Configures Claude hooks when missing
  - Previously only updated the script file while showing but ignoring other issues

### 📝 Internal

- Added logic to UpdateFlow to handle all detected installation issues
- Updater no longer just shows problems - it fixes them

## [0.1.4] - 2025-08-03

### 🐛 Fixed

- **Models directory location**: Kokoro models now correctly install in `~/.claude/ccnotify/models` instead of current directory
  - Installer changes directory before running setup_kokoro
  - Config file now includes correct models_dir path
- **Hardcoded paths removed**: Removed all hardcoded references to old `~/.claude/hooks` directory
  - Updated BASE_DIR to use `~/.claude/ccnotify`
  - notify.py now reads models_dir from config.json
  - Prevents creation of unwanted hooks directory

### 📝 Internal

- TTS provider initialization now properly reads configuration from config.json
- Better handling of models directory path in Kokoro provider

## [0.1.3] - 2025-08-03

### 🐛 Fixed

- **Installation test error**: Fixed "'PosixPath' object has no attribute 'get'" error during Kokoro setup
  - KokoroProvider now receives proper config dictionary instead of bare Path object
  - Installation test properly checks if models are available

## [0.1.2] - 2025-08-03

### 🐛 Fixed

- **Critical installer bug**: Fixed "models" variable reference before definition in setup.py
- **Installation failure handling**: Installer now properly stops when model downloads fail
  - Returns None instead of config dict on Kokoro setup failures
  - Shows clear error messages and prompts for alternative providers
  - Prevents Kokoro installation without required model files

### ✨ Added

- **Local testing workflow**: Added comprehensive installer test suite
  - Created `scripts/test_installer.py` for local testing
  - Added GitHub Actions workflow for automated testing
  - Tests cover fresh install, update flow, migration, and error scenarios

### 📝 Internal

- Improved error propagation throughout installation flow
- Better user feedback when TTS provider setup fails

### ⚠️ Breaking Changes

- Minimum Python version is now 3.10 (was 3.9) due to onnxruntime dependency requirements

## [0.1.1] - 2025-08-03

### 🐛 Fixed

- **Critical installer bug**: Fixed Rich Text concatenation error that caused UpdateFlow to crash when existing installations were detected
  - Changed from `Text.append(Align)` to `Group` composition in welcome screen
  - Installer now properly displays ANSI Shadow welcome screen and status tables
  - Both first-time installation and update flows work correctly

### 📝 Internal

- Improved error handling in version comparison utilities when `packaging` module is not available

## [0.1.0] - 2025-08-03

### 🎉 Initial Release

This is the first public release of CCNotify - a Voice Notification System for Claude Code.

### ✨ Features

#### Single-Command Installer
- **Simplified CLI**: One intelligent command `uvx ccnotify install` handles all scenarios
- **ANSI Shadow Welcome**: Beautiful ASCII art welcome screen with gradient colors
- **Automatic Detection**: Intelligently detects existing installations vs first-time setup
- **Rich User Experience**: Interactive TTS provider selection with progress indicators

#### TTS (Text-to-Speech) Support
- **Local TTS**: Kokoro ONNX models with 50+ voices (privacy-focused, ~350MB)
- **Cloud TTS**: ElevenLabs API integration (premium quality)
- **Smart Caching**: Audio file caching by content hash to prevent regeneration
- **Flexible Configuration**: JSON-based configuration with sensible defaults

#### Intelligent Notifications
- **Smart Filtering**: Only notifies for significant events, not routine operations
- **Project Detection**: Automatically identifies current project from Claude session
- **Risk Awareness**: Alerts for potentially dangerous commands (file deletions, etc.)
- **Multi-Event Support**: Handles PreToolUse, PostToolUse, Stop, SubagentStop, Notification events

#### Installation & Updates
- **Automatic Migration**: Migrates legacy `~/.claude/hooks/` to `~/.claude/ccnotify/`
- **Version Management**: Semantic versioning with intelligent update detection
- **Backup & Rollback**: Creates backups before updates with rollback on failure
- **Settings Integration**: Automatically configures Claude Code hooks with backup

### 🛠️ Technical Implementation

#### Architecture
- **Modular Design**: Separated installer, TTS providers, and core notification logic
- **Factory Pattern**: TTS provider selection with automatic fallbacks
- **Rich Console**: Professional CLI styling with progress bars and status displays
- **Error Handling**: Comprehensive error recovery with graceful degradation

#### Platform Support
- **macOS**: Full support with native notifications (pync) and audio playback (afplay)
- **Linux**: Partial support with plyer notifications (audio playback pending)
- **Windows**: Not yet implemented

#### Dependencies
- **Core**: Rich, requests, pync/plyer, python-dotenv
- **TTS**: kokoro-onnx, pydub, soundfile
- **Optional**: elevenlabs (for cloud TTS)
- **Utils**: tqdm, pathlib2 (for Python < 3.11)

### 📋 Requirements

- **Python**: 3.9+ 
- **Platform**: macOS or Linux
- **Claude Code**: CLI installed and configured
- **Storage**: ~350MB for local TTS models (optional)
- **Network**: Internet connection for ElevenLabs TTS (optional)

### 🚀 Installation

```bash
uvx ccnotify install
```

The installer will guide you through:
1. TTS provider selection (Kokoro/ElevenLabs/None)
2. Model downloads (if needed)
3. Claude Code integration
4. Configuration setup

### 🔧 Configuration

Configuration is stored in `~/.claude/ccnotify/config.json`:

**Kokoro (Local TTS):**
```json
{
  "tts_provider": "kokoro",
  "kokoro": {
    "voice": "af_sarah",
    "speed": 1.0
  }
}
```

**ElevenLabs (Cloud TTS):**
```json
{
  "tts_provider": "elevenlabs", 
  "elevenlabs": {
    "api_key": "your_key_here",
    "voice_id": "21m00Tcm4TlvDq8ikWAM"
  }
}
```

### 📝 Known Limitations

- **Platform Support**: Full functionality only tested on macOS
- **Import Dependencies**: Some optional dependencies may need manual resolution
- **Model Storage**: Large TTS models not included in package (downloaded separately)

### 🙏 Acknowledgments

- [Kokoro TTS](https://github.com/thewh1teagle/kokoro-onnx) for local voice synthesis
- [ElevenLabs](https://elevenlabs.io) for premium cloud TTS
- [Rich](https://github.com/Textualize/rich) for beautiful console output

---

**Breaking Changes**: This is an initial release, so no breaking changes yet.

**Migration**: First-time installation - no migration needed.

[0.1.5]: https://github.com/Helmi/ccnotify/releases/tag/v0.1.5
[0.1.4]: https://github.com/Helmi/ccnotify/releases/tag/v0.1.4
[0.1.3]: https://github.com/Helmi/ccnotify/releases/tag/v0.1.3
[0.1.2]: https://github.com/Helmi/ccnotify/releases/tag/v0.1.2
[0.1.1]: https://github.com/Helmi/ccnotify/releases/tag/v0.1.1
[0.1.0]: https://github.com/Helmi/ccnotify/releases/tag/v0.1.0