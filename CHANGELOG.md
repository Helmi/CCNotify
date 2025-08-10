# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.13] - 2025-08-10

### Fixed
- NotebookEdit operations no longer trigger false error notifications
- Input needed alerts only appear for actual permission requests
- Empty error fields in tool responses are now properly ignored
- Platform compatibility prompts now respect quiet mode

### Added
- Optional logging with `--logging` flag during installation
- Debug logging for notification triggers to help troubleshooting
- Keyword filtering for permission-related notifications

### Changed
- Error detection logic now checks for non-empty error values
- Notification filtering improved to reduce false positives
- Refactored replacements.json structure to eliminate duplication
- Updated default Kokoro voice to af_heart

## [0.1.12] - 2025-08-04

### Added
- Optional logging with `--logging` flag during installation
- Log rotation to prevent large log files (10MB max, keeps last 5 files)
- Comprehensive test suite for logging functionality

### Changed
- Logging is now disabled by default to prevent disk space issues
- Optimized CI to test only Python 3.10 to save GitHub Actions minutes

### Fixed
- Installer tests no longer timeout due to model downloads
- Platform compatibility prompts respect quiet mode

## [0.1.11] - 2025-08-03

### Fixed
- TTS pronunciation now uses values from replacements.json
- Sound file names no longer include TTS provider prefix

## [0.1.10] - 2025-08-02

### Added
- Version checking and update notifications in installer
- Automatic migration from legacy hooks directory

### Fixed
- Installer flow for first-time users
- Config file initialization issues

## [0.1.9] - 2025-08-01

### Added
- Non-interactive installation mode
- Quiet mode for CI/testing environments

### Changed
- Improved error handling in TTS providers
- Better project name detection from Claude sessions

## [0.1.0] - 2025-07-20

### Initial Release

First public release of CCNotify - Voice Notification System for Claude Code

#### Features
- Single-command installer with ANSI Shadow welcome screen
- Local TTS support via Kokoro ONNX models (50+ voices)
- Cloud TTS support via ElevenLabs API
- Smart notification filtering for significant events
- Automatic project detection from Claude sessions
- Audio file caching by content hash
- JSON-based configuration

#### Platform Support
- macOS: Full support (pync notifications + afplay audio)
- Linux: Partial support (plyer notifications)
- Windows: Not yet implemented