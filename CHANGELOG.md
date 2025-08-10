# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

## [0.1.12] - 2025-08-04

Initial public release of CCNotify - Voice Notification System for Claude Code