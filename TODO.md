# CCNotify TODO List

## High Priority
- [x] Copy notification system files from ~/.claude/hooks to project folder
- [x] Create docs/ folder with project documentation  
- [x] Create todo.md file for tracking tasks
- [ ] Initialize git repository and create .gitignore
- [ ] Create public ccnotify repo on GitHub

## Medium Priority
- [ ] Make logging optional through .env (default off)
- [ ] Clean up replacements.json to be more generic
- [ ] Review code structure and refactor if needed
- [ ] Create comprehensive README.md

## Low Priority
- [ ] Review sound generation/caching system
- [ ] Add alternative TTS options (local, free APIs)
- [ ] Add Windows compatibility for notifications

## Future Enhancements
- [ ] Add Linux support for notifications
- [ ] Create configuration wizard/setup script
- [ ] Add support for custom notification sounds
- [ ] Create tests for core functionality
- [ ] Add webhook support for external integrations
- [ ] Support for notification grouping/batching
- [ ] Add quiet hours/DND mode support
- [ ] Create brew formula for easy installation
- [ ] Add notification history viewer
- [ ] Support for different notification urgency levels

## Technical Debt
- [ ] Improve error handling and recovery
- [ ] Add type hints throughout the codebase
- [ ] Create proper Python package structure
- [ ] Add CI/CD pipeline
- [ ] Improve documentation with examples
- [ ] Performance optimization for transcript reading
- [ ] Add metrics/telemetry (opt-in)

## Platform Support
- [ ] Windows: Research notification options (Windows Toast, plyer, etc.)
- [ ] Linux: Add support for notify-send/libnotify
- [ ] Cross-platform TTS alternatives to macOS `say`
- [ ] Investigate cross-platform sound playback options

## Integration Ideas
- [ ] VSCode extension integration
- [ ] Slack/Discord webhook support
- [ ] Email notifications for critical events
- [ ] Mobile push notifications
- [ ] Integration with other AI coding assistants