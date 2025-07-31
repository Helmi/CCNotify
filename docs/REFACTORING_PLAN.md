# CCNotify Refactoring Plan

## Current Structure Issues

1. **Monolithic Design**: All functionality in single notify.py file
2. **Tight Coupling**: Hard dependencies between components
3. **Limited Testability**: Global state and direct file I/O
4. **Platform-Specific**: macOS-only implementation

## Proposed Module Structure

```
ccnotify/
├── ccnotify/
│   ├── __init__.py
│   ├── config.py         # Configuration management
│   ├── notifications/
│   │   ├── __init__.py
│   │   ├── base.py       # Abstract notifier
│   │   ├── macos.py      # macOS implementation
│   │   ├── windows.py    # Windows implementation (future)
│   │   └── linux.py      # Linux implementation (future)
│   ├── tts/
│   │   ├── __init__.py
│   │   ├── base.py       # Abstract TTS provider
│   │   ├── macos_say.py  # macOS say command
│   │   ├── elevenlabs.py # ElevenLabs API
│   │   └── local.py      # Local alternatives (future)
│   ├── cache.py          # Project/session caching
│   ├── replacements.py   # Text replacement logic
│   └── handlers.py       # Hook event handlers
├── notify.py             # Main entry point (thin wrapper)
└── tests/                # Unit tests
```

## Refactoring Benefits

1. **Modularity**: Each component has single responsibility
2. **Extensibility**: Easy to add new platforms/TTS providers
3. **Testability**: Mock dependencies, test in isolation
4. **Maintainability**: Smaller, focused modules

## Implementation Priority

Given current project goals, we should:
1. Keep current structure for MVP
2. Document refactoring plan for future
3. Focus on completing core features first
4. Refactor after initial release and user feedback

## Decision: Defer Refactoring

For now, we'll maintain the current structure because:
- It works well for the current use case
- Refactoring would delay initial release
- Better to get user feedback first
- Can refactor based on real usage patterns