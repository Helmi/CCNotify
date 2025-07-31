# CCNotify

🔔 Intelligent notification system for Claude Code with audio feedback

CCNotify enhances your Claude Code experience by providing smart, context-aware notifications for tool usage and execution events. It filters out routine operations and only alerts you to important events, with optional text-to-speech support.

## Features

- **Smart Filtering**: Only notifies for potentially dangerous operations (rm, mv, sudo, etc.)
- **Project Context**: Automatically detects and includes project name in notifications
- **Audio Feedback**: Optional TTS using macOS `say` command or ElevenLabs API
- **Customizable**: Configure project names, command descriptions, and notification behavior
- **Lightweight**: Minimal dependencies, fast execution
- **Privacy-Focused**: All processing happens locally, optional logging

## Quick Start

1. **Install CCNotify**:
   ```bash
   git clone https://github.com/Helmi/ccnotify.git
   cd ccnotify
   ```

2. **Copy files to Claude Code hooks directory**:
   ```bash
   cp notify.py ~/.claude/hooks/
   cp replacements.json ~/.claude/hooks/
   
   # Make scripts executable
   chmod +x ~/.claude/hooks/notify.py
   ```

3. **Configure Claude Code** (`~/.claude/settings.json`):
   ```json
   {
     "hooks": {
       "PreToolUse": [
         {
           "matcher": "Bash|Write|MultiEdit|Edit",
           "hooks": [
             {
               "type": "command",
               "command": "uv run ~/.claude/hooks/notify.py"
             }
           ]
         }
       ],
       "PostToolUse": [
         {
           "matcher": ".*",
           "hooks": [
             {
               "type": "command",
               "command": "uv run ~/.claude/hooks/notify.py"
             }
           ]
         }
       ],
       "Stop": [
         {
           "matcher": ".*",
           "hooks": [
             {
               "type": "command",
               "command": "uv run ~/.claude/hooks/notify.py"
             }
           ]
         }
       ],
       "SubagentStop": [
         {
           "matcher": ".*",
           "hooks": [
             {
               "type": "command",
               "command": "uv run ~/.claude/hooks/notify.py"
             }
           ]
         }
       ],
       "Notification": [
         {
           "matcher": ".*",
           "hooks": [
             {
               "type": "command",
               "command": "uv run ~/.claude/hooks/notify.py"
             }
           ]
         }
       ]
     }
   }
   ```

4. **Optional: Configure environment** (create `~/.claude/hooks/.env`):
   ```bash
   # Copy example configuration
   cp .env.example ~/.claude/hooks/.env
   
   # Edit with your preferences
   nano ~/.claude/hooks/.env
   ```

## Configuration

### Environment Variables (.env)

- `USE_TTS`: Enable text-to-speech (default: false)
- `USE_LOGGING`: Enable debug logging (default: false)
- `ELEVENLABS_API_KEY`: Your ElevenLabs API key (optional)
- `ELEVENLABS_VOICE_ID`: Voice selection (default: Rachel)
- `ELEVENLABS_MODEL_ID`: Model selection (default: eleven_flash_v2_5)

### Customizing Notifications (replacements.json)

Edit `~/.claude/hooks/replacements.json` to customize:

1. **Project Names**: Map folder names to friendly names
   ```json
   "project_names": {
     "replacements": {
       "myproject": "My Awesome Project",
       "work": "Work Projects"
     }
   }
   ```

2. **Command Descriptions**: Customize how commands are announced
   ```json
   "commands": {
     "replacements": {
       "rm": "deleting files",
       "docker": "managing containers"
     }
   }
   ```

## Notification Types

- **🔧 Tool Activity**: Dangerous commands (rm, mv, sudo, system file edits)
- **✅ Execution Complete**: Task completion notifications
- **⚠️ Input Needed**: When Claude needs permission
- **❌ Error**: Tool failures and errors
- **🤖 Subagent Done**: Background task completion

## Requirements

- macOS (currently, Windows/Linux support planned)
- Python 3.9+
- Claude Code CLI
- Optional: ElevenLabs API account for premium TTS

## Advanced Usage

### Test Notifications

```bash
# Test different notification types
python ~/.claude/hooks/notify.py tool_activity "Testing dangerous command"
python ~/.claude/hooks/notify.py execution_complete "Task finished"
python ~/.claude/hooks/notify.py error "Something went wrong"
```

### View Logs (when enabled)

```bash
tail -f ~/.claude/hooks/logs/notifications_$(date +%Y%m%d).log
```

## Troubleshooting

1. **No notifications appearing**: 
   - Check that scripts are executable: `chmod +x ~/.claude/hooks/*.py ~/.claude/hooks/*.sh`
   - Verify hook configuration in Claude Code settings
   - Enable logging to debug: `USE_LOGGING=true` in .env

2. **TTS not working**:
   - Ensure `USE_TTS=true` in .env
   - For ElevenLabs: Check API key is valid
   - Test macOS say: `say "Hello world"`

3. **Wrong project names**:
   - Check session cache: `~/.claude/hooks/session_project_cache.json`
   - Update replacements.json with your project mappings

## Contributing

Contributions are welcome! Please see [TODO.md](TODO.md) for planned features and improvements.

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built for [Claude Code](https://claude.ai) by Anthropic
- Inspired by the need for better awareness during AI-assisted coding
- Thanks to the Claude Code community for feedback and ideas