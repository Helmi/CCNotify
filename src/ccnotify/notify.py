#!/usr/bin/env python3
__version__ = "0.1.12"

# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "pync",
#     "requests",
#     "python-dotenv",
#     "kokoro-onnx",
#     "pydub",
#     "soundfile",
#     "tqdm"
# ]
# ///

"""
CCNotify - Intelligent notification system for Claude Code with audio feedback
Enhanced version with modular TTS provider system
"""

import json
import sys
import os
import subprocess
import hashlib
import datetime
import logging
import time
import glob
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

try:
    import pync
    import requests
    from pydub import AudioSegment
    from pydub.playback import play
    from dotenv import load_dotenv
except ImportError:
    # Dependencies will be auto-installed via uv
    pass

# Embedded Kokoro TTS provider for standalone usage
import io
import hashlib


class KokoroTTSProvider:
    """Minimal embedded Kokoro TTS provider"""

    def __init__(self, models_dir: Path):
        self.models_dir = Path(models_dir)
        self.model_path = self.models_dir / "kokoro-v1.0.onnx"
        self.voices_path = self.models_dir / "voices-v1.0.bin"
        self._kokoro = None
        self.voice = "af_heart"  # Better default voice
        self.speed = 1.0
        self.format = "mp3"  # Default to MP3
        self.mp3_bitrate = "128k"

    def is_available(self) -> bool:
        """Check if Kokoro is available"""
        try:
            # Check model files exist
            if not self.model_path.exists():
                logger.warning(f"Kokoro model not found: {self.model_path}")
                return False
            if not self.voices_path.exists():
                logger.warning(f"Kokoro voices not found: {self.voices_path}")
                return False

            # Try to import kokoro
            from kokoro_onnx import Kokoro

            self._kokoro = Kokoro(str(self.model_path), str(self.voices_path))
            logger.debug(f"Kokoro TTS initialized successfully with models from {self.models_dir}")
            return True
        except ImportError as e:
            logger.warning(f"Kokoro import failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Kokoro initialization failed: {e}")
            return False

    def get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        return hashlib.md5(text.encode()).hexdigest()[:16]

    def get_file_extension(self) -> str:
        """Get file extension based on format"""
        if self.format == "mp3":
            return ".mp3"
        elif self.format == "aiff":
            return ".aiff"
        else:
            return ".wav"

    def generate(self, text: str, output_path: Path) -> bool:
        """Generate TTS audio"""
        try:
            if not self._kokoro:
                from kokoro_onnx import Kokoro

                self._kokoro = Kokoro(str(self.model_path), str(self.voices_path))

            # Generate audio with Kokoro (returns numpy array and sample rate)
            audio_array, sample_rate = self._kokoro.create(
                text=text, voice=self.voice, speed=self.speed
            )

            # Convert numpy array to WAV bytes
            import soundfile

            wav_buffer = io.BytesIO()
            soundfile.write(wav_buffer, audio_array, sample_rate, format="WAV")
            audio_data = wav_buffer.getvalue()

            # Save based on format
            if self.format == "mp3":
                # Convert to MP3 using pydub
                try:
                    from pydub import AudioSegment

                    audio = AudioSegment.from_wav(io.BytesIO(audio_data))
                    audio.export(str(output_path), format="mp3", bitrate=self.mp3_bitrate)
                except ImportError:
                    # Fallback to WAV if pydub not available
                    output_path = output_path.with_suffix(".wav")
                    with open(output_path, "wb") as f:
                        f.write(audio_data)
            else:
                # Save as WAV
                with open(output_path, "wb") as f:
                    f.write(audio_data)

            return True

        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            return False


# Configuration
BASE_DIR = Path.home() / ".claude" / "ccnotify"
SOUNDS_DIR = BASE_DIR / "sounds"
LOGS_DIR = BASE_DIR / "logs"
CACHE_FILE = BASE_DIR / "session_project_cache.json"
REPLACEMENTS_FILE = BASE_DIR / "replacements.json"
PENDING_COMMANDS_FILE = BASE_DIR / "pending_commands_cache.json"
PROJECTS_DIR = Path.home() / ".claude" / "projects"

SOUNDS_DIR.mkdir(parents=True, exist_ok=True)

# Environment variables (will be reloaded in main() if .env exists)
USE_TTS = os.getenv("USE_TTS", "true").lower() == "true"  # Default to true to use TTS providers
USE_LOGGING = os.getenv("USE_LOGGING", "false").lower() == "true"
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "kokoro")  # Options: macos_say, elevenlabs, kokoro
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Rachel
ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_flash_v2_5")  # Flash 2.5
KOKORO_VOICE = os.getenv("KOKORO_VOICE", "af_heart")
# KOKORO_PATH is now determined from config file
KOKORO_SPEED = os.getenv("KOKORO_SPEED", "1.0")  # Speed multiplier (0.5-2.0)


# Create a no-op logger class for when logging is disabled
class NoOpLogger:
    def debug(self, msg, *args, **kwargs):
        pass

    def info(self, msg, *args, **kwargs):
        pass

    def warning(self, msg, *args, **kwargs):
        pass

    def error(self, msg, *args, **kwargs):
        pass

    def critical(self, msg, *args, **kwargs):
        pass


# Setup logging (will be configured properly in setup_logging())
logger = NoOpLogger()

# Cache settings
CACHE_EXPIRY_DAYS = 7  # Keep cache entries for 7 days


def setup_logging(enable_logging=None):
    """Setup logging based on --logging flag or USE_LOGGING environment variable"""
    global logger

    # Command-line flag takes precedence over environment variable
    if enable_logging is None:
        enable_logging = USE_LOGGING

    if enable_logging:
        try:
            # Create logs directory only if logging is enabled
            LOGS_DIR.mkdir(parents=True, exist_ok=True)

            log_file = LOGS_DIR / f"notifications_{datetime.datetime.now().strftime('%Y%m%d')}.log"

            # Check log file size and rotate if needed (max 10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            if log_file.exists() and log_file.stat().st_size > max_size:
                # Rotate the log file
                backup_file = log_file.with_suffix(
                    f'.{datetime.datetime.now().strftime("%H%M%S")}.log'
                )
                log_file.rename(backup_file)

                # Clean up old log files (keep last 5)
                log_files = sorted(
                    LOGS_DIR.glob("notifications_*.log"), key=lambda f: f.stat().st_mtime
                )
                if len(log_files) > 5:
                    for old_file in log_files[:-5]:
                        old_file.unlink()

            logging.basicConfig(
                level=logging.DEBUG,
                format="%(asctime)s - %(levelname)s - %(message)s",
                handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stderr)],
                force=True,  # Force reconfiguration
            )
            logger = logging.getLogger(__name__)
            logger.info("Logging enabled")
        except (OSError, PermissionError) as e:
            # Fall back to no-op logger if we can't create log directory
            logger = NoOpLogger()
            print(f"Warning: Could not enable logging: {e}", file=sys.stderr)
    else:
        # Keep the no-op logger
        logger = NoOpLogger()


def load_project_cache() -> Dict[str, Dict[str, Any]]:
    """Load the project cache from disk"""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
    return {}


def save_project_cache(cache: Dict[str, Dict[str, Any]]):
    """Save the project cache to disk"""
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to save cache: {e}")


def clean_old_cache_entries(cache: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Remove cache entries older than CACHE_EXPIRY_DAYS"""
    current_time = time.time()
    expiry_seconds = CACHE_EXPIRY_DAYS * 24 * 60 * 60

    cleaned_cache = {}
    for session_id, data in cache.items():
        if current_time - data.get("timestamp", 0) < expiry_seconds:
            cleaned_cache[session_id] = data

    return cleaned_cache


def decode_project_folder_name(folder_name: str) -> Optional[str]:
    """
    Decode project folder name to actual path
    -Users-helmi-code-paperless-ai → /Users/helmi/code/paperless-ai
    """
    if not folder_name.startswith("-"):
        return None

    # Remove leading dash and split
    parts = folder_name[1:].split("-")

    # Reconstruct path with proper separators
    path = "/" + "/".join(parts)
    return path


def is_cwd_under_project(cwd: str, project_path: str) -> bool:
    """Check if current working directory is under the project path"""
    try:
        cwd_path = Path(cwd).resolve()
        project_path_obj = Path(project_path).resolve()
        return project_path_obj in cwd_path.parents or cwd_path == project_path_obj
    except Exception:
        return False


def auto_add_project_to_replacements(project_name: str, folder_name: str = None):
    """Automatically add project to replacements.json if not present"""
    try:
        replacements = load_replacements()
        projects = replacements.get("projects", {})

        # Check if project already exists (case-insensitive)
        exists = any(project_name.lower() == key.lower() for key in projects.keys())

        if not exists:
            # Create pronunciation-friendly version (replace hyphens with spaces)
            friendly_name = project_name.replace("-", " ")

            # Add to projects section with rich metadata
            projects[project_name] = {
                "folder": folder_name,
                "display_name": project_name,
                "pronunciation": friendly_name,
            }

            # Ensure structure exists
            if "projects" not in replacements:
                replacements["projects"] = {}
            replacements["projects"] = projects

            # Save back to file
            with open(REPLACEMENTS_FILE, "w") as f:
                json.dump(replacements, f, indent=2)

            logger.info(
                f"Auto-added project '{project_name}' to replacements (pronounce as '{friendly_name}')"
            )

    except Exception as e:
        logger.warning(f"Failed to auto-add project to replacements: {e}")


def resolve_project_name(session_id: str, cwd: str = None) -> str:
    """Resolve project name from session ID with cwd validation"""
    # Load and clean cache
    cache = load_project_cache()
    cache = clean_old_cache_entries(cache)

    # Check if we have a cached result
    if session_id in cache:
        cached_name = cache[session_id]["project_name"]

        # If we have cwd, validate the cache is still correct
        if cwd and "project_path" in cache[session_id]:
            cached_path = cache[session_id]["project_path"]
            if not is_cwd_under_project(cwd, cached_path):
                logger.warning(
                    f"Cached project {cached_name} doesn't match cwd {cwd}, re-resolving"
                )
                # Continue to re-resolve
            else:
                logger.debug(f"Found cached project name for session {session_id}: {cached_name}")
                return cached_name
        else:
            logger.debug(f"Found cached project name for session {session_id}: {cached_name}")
            return cached_name

    # Search for the session file in project folders
    try:
        session_file = f"{session_id}.jsonl"
        pattern = str(PROJECTS_DIR / "*" / session_file)
        matches = glob.glob(pattern)

        if matches:
            # Get the project folder name
            project_path = Path(matches[0]).parent
            folder_name = project_path.name

            # Decode the folder name to get actual project path
            actual_project_path = decode_project_folder_name(folder_name)

            if actual_project_path:
                # Extract meaningful project name from the actual path
                # For paths like /Users/helmi/code/agent/zero, we want "zero" or "agent-zero"
                path_parts = Path(actual_project_path).parts

                # Look for common project parent directories
                common_parents = [
                    "code",
                    "projects",
                    "dev",
                    "work",
                    "repos",
                    "src",
                    "Documents",
                    "Desktop",
                ]
                project_name = Path(actual_project_path).name  # Default to last part

                # Try to find a more meaningful project name
                for i, part in enumerate(path_parts):
                    if part in common_parents and i + 1 < len(path_parts):
                        # Use everything after the common parent as the project name
                        remaining_parts = path_parts[i + 1 :]
                        if len(remaining_parts) == 1:
                            project_name = remaining_parts[0]
                        else:
                            # For nested projects like code/agent/zero, use "agent-zero" or just "zero"
                            # depending on the depth
                            if len(remaining_parts) == 2:
                                # Use hyphenated form for two-level projects
                                project_name = "-".join(remaining_parts)
                            else:
                                # For deeper nesting, just use the last part
                                project_name = remaining_parts[-1]
                        break

                # Validate against cwd if provided
                if cwd and not is_cwd_under_project(cwd, actual_project_path):
                    logger.warning(
                        f"CWD {cwd} doesn't appear to be under project {actual_project_path}"
                    )
                    # Still proceed but log the warning

                # Auto-add to replacements if not present
                auto_add_project_to_replacements(project_name, folder_name)

                # Cache the result
                cache[session_id] = {
                    "project_name": project_name,
                    "timestamp": time.time(),
                    "project_path": actual_project_path,
                    "claude_folder": folder_name,
                }
                save_project_cache(cache)

                logger.debug(
                    f"Resolved project name for session {session_id}: {project_name} (from {actual_project_path})"
                )
                return project_name
            else:
                logger.warning(f"Could not decode project folder name: {folder_name}")

    except Exception as e:
        logger.warning(f"Error resolving project name: {e}")

    return "unknown"


def migrate_replacements_format(old_data: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate from old replacements format to new unified structure"""
    new_data = {"projects": {}, "commands": {}, "patterns": []}

    # Migrate auto-discovered projects
    if "_auto_discovered" in old_data:
        auto_projects = old_data["_auto_discovered"].get("projects", {})
        for proj_name, proj_info in auto_projects.items():
            new_data["projects"][proj_name] = {
                "folder": proj_info.get("folder"),
                "display_name": proj_info.get("display_name", proj_name),
                "pronunciation": proj_info.get("pronunciation", proj_name),
            }

    # Migrate project_names replacements (if not already in projects)
    if "project_names" in old_data:
        project_replacements = old_data["project_names"].get("replacements", {})
        for proj_name, pronunciation in project_replacements.items():
            if proj_name not in new_data["projects"]:
                new_data["projects"][proj_name] = {
                    "folder": None,  # Will be filled on next auto-discovery
                    "display_name": proj_name,
                    "pronunciation": pronunciation,
                }

    # Migrate commands
    if "commands" in old_data:
        cmd_replacements = old_data["commands"].get("replacements", {})
        new_data["commands"] = cmd_replacements

    # Migrate patterns
    if "patterns" in old_data:
        pattern_replacements = old_data["patterns"].get("replacements", [])
        new_data["patterns"] = pattern_replacements

    # Add default commands if empty
    if not new_data["commands"]:
        new_data["commands"] = {
            "ls": "list",
            "cd": "change directory",
            "rm": "remove",
            "mkdir": "make directory",
            "npm": "N P M",
            "uvx": "U V X",
        }

    # Add default patterns if empty
    if not new_data["patterns"]:
        new_data["patterns"] = [
            {"pattern": "npm run (\\w+)", "replacement": "N P M run {1}"},
            {"pattern": "git (push|pull|commit)", "replacement": "git {1}"},
            {"pattern": "(.+)\\.py", "replacement": "{1} python file"},
        ]

    return new_data


def load_replacements() -> Dict[str, Any]:
    """Load replacements configuration with automatic migration from old format"""
    if REPLACEMENTS_FILE.exists():
        try:
            with open(REPLACEMENTS_FILE, "r") as f:
                data = json.load(f)

            # Check if migration is needed (old format detection)
            needs_migration = False
            if "project_names" in data and "replacements" in data.get("project_names", {}):
                needs_migration = True
            elif "_auto_discovered" in data:
                needs_migration = True

            if needs_migration:
                # Migrate from old format to new format
                migrated = migrate_replacements_format(data)
                # Save migrated format
                with open(REPLACEMENTS_FILE, "w") as f:
                    json.dump(migrated, f, indent=2)
                logger.info("Migrated replacements.json to new format")
                return migrated

            return data
        except Exception as e:
            logger.warning(f"Failed to load replacements: {e}")

    # Return new default structure
    return {
        "projects": {},
        "commands": {
            "ls": "list",
            "cd": "change directory",
            "rm": "remove",
            "mkdir": "make directory",
            "npm": "N P M",
            "uvx": "U V X",
        },
        "patterns": [
            {"pattern": "npm run (\\w+)", "replacement": "N P M run {1}"},
            {"pattern": "git (push|pull|commit)", "replacement": "git {1}"},
            {"pattern": "(.+)\\.py", "replacement": "{1} python file"},
        ],
    }


def apply_project_name_replacement(project_name: str, replacements: Dict[str, Any]) -> str:
    """Apply project name replacement for display"""
    # Look up in projects section
    projects = replacements.get("projects", {})

    # Case-insensitive matching
    for proj_key, proj_data in projects.items():
        if project_name.lower() == proj_key.lower():
            return proj_data.get("display_name", project_name)

    return project_name


def get_project_pronunciation(project_name: str, replacements: Dict[str, Any]) -> str:
    """Get the pronunciation for a project name for TTS"""
    # Look up in projects section
    projects = replacements.get("projects", {})
    for proj_key, proj_data in projects.items():
        if proj_key.lower() == project_name.lower():
            return proj_data.get("pronunciation", project_name)

    return project_name


def apply_command_replacement(command: str, replacements: Dict[str, Any]) -> str:
    """Apply command replacement for audio"""
    cmd_replacements = replacements.get("commands", {})
    pattern_replacements = replacements.get("patterns", [])

    # First check pattern replacements
    for pattern_config in pattern_replacements:
        pattern = pattern_config.get("pattern", "")
        replacement = pattern_config.get("replacement", "")
        if pattern and replacement:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                # Handle group replacements like $1
                result = replacement
                for i, group in enumerate(match.groups(), 1):
                    result = result.replace(f"${i}", group)
                return result

    # Then check direct command replacements
    cmd_parts = command.split()
    if cmd_parts:
        base_cmd = cmd_parts[0]
        if base_cmd in cmd_replacements:
            return cmd_replacements[base_cmd]

    # Return the original command if no replacement found
    return f"running {cmd_parts[0]}" if cmd_parts else "running command"


class NotificationHandler:
    def __init__(self):
        self.sounds_cache = {}
        self.tts_provider = None
        self._init_tts_provider()

    def _init_tts_provider(self):
        """Initialize TTS provider"""
        if not USE_TTS:
            logger.debug("TTS disabled")
            return

        try:
            # Load configuration file
            config_file = BASE_DIR / "config.json"
            config = {}
            if config_file.exists():
                try:
                    with open(config_file) as f:
                        config = json.load(f)
                except Exception:
                    pass

            # Use embedded Kokoro provider
            if TTS_PROVIDER == "kokoro":
                models_dir = config.get("models_dir", str(BASE_DIR / "models"))
                self.tts_provider = KokoroTTSProvider(models_dir)

                # Configure from environment/config
                self.tts_provider.voice = config.get("voice", KOKORO_VOICE)
                self.tts_provider.speed = float(config.get("speed", KOKORO_SPEED))
                self.tts_provider.format = config.get("format", "mp3").lower()
                self.tts_provider.mp3_bitrate = config.get("mp3_bitrate", "128k")

                if self.tts_provider.is_available():
                    logger.info(f"Initialized embedded Kokoro TTS provider")
                else:
                    logger.warning("Kokoro TTS not available - models may not be downloaded")
                    self.tts_provider = None
            else:
                logger.warning(f"Unsupported TTS provider: {TTS_PROVIDER}")
                self.tts_provider = None

        except Exception as e:
            logger.error(f"Failed to initialize TTS provider: {e}")
            self.tts_provider = None

    def notify(self, title: str, message: str, sound_name: str = "Glass"):
        """Display macOS notification - simple and clean"""
        try:
            pync.notify(message=message, title=title, sound=sound_name)
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    def play_sound_file(self, sound_path: Path):
        """Play a sound file using macOS afplay"""
        if sound_path.exists():
            try:
                subprocess.Popen(["afplay", str(sound_path)])
            except Exception as e:
                logger.error(f"Failed to play sound: {e}")

    def get_notification_sound(self, event_type: str, custom_text: str = "") -> Optional[Path]:
        """Get or generate sound for notification"""
        if not USE_TTS or not self.tts_provider:
            logger.warning("TTS not available - no sound will be played")
            return None

        # Default texts for each event type
        default_texts = {
            "tool_activity": "Tool activity",
            "execution_complete": "Task complete",
            "subagent_done": "Sub agent done",
            "error": "Error occurred",
            "tool_blocked": "Tool blocked",
            "compaction": "Compacting context",
            "input_needed": "Input needed",
        }

        # Determine text to speak
        text_to_speak = (
            custom_text if custom_text else default_texts.get(event_type, "Claude notification")
        )
        logger.debug(f"TTS text: '{text_to_speak}'")

        # Generate cache key and file path
        cache_key = self.tts_provider.get_cache_key(text_to_speak)
        file_extension = self.tts_provider.get_file_extension()
        sound_file = SOUNDS_DIR / f"{event_type}_{cache_key}{file_extension}"

        # Use cached file if exists
        if sound_file.exists():
            logger.debug(f"Using cached sound: {sound_file}")
            return sound_file

        # Generate new sound file
        try:
            success = self.tts_provider.generate(text_to_speak, sound_file)
            if success:
                logger.info(f"Generated {TTS_PROVIDER} TTS: {text_to_speak}")
                return sound_file
            else:
                logger.warning(f"TTS generation failed")
                return None

        except Exception as e:
            logger.error(f"TTS generation error: {e}")
            return None

    def handle_hook(self, hook_data: Dict[str, Any]):
        """Process hook data and generate appropriate notification"""
        # Claude Code uses "event" field, not "hook_event_name"
        hook_type = hook_data.get("event", hook_data.get("hook_event_name", "unknown"))
        logger.info(f"Processing hook type: {hook_type}")

        # Log all available fields for this hook type
        logger.debug(f"Available fields: {list(hook_data.keys())}")

        event_type = None
        message = None
        custom_tts = None

        # Load replacements configuration
        replacements = load_replacements()

        # Extract session context - Claude Code uses camelCase "sessionId"
        session_id = hook_data.get("sessionId", hook_data.get("session_id", "unknown"))
        cwd = hook_data.get("cwd", os.getcwd())  # Fall back to current working directory

        # If no session ID but we have cwd, try to extract project name from path
        if session_id == "unknown" and cwd:
            # Try to extract project name from cwd
            path_parts = Path(cwd).parts
            # Look for common project directories
            if "code" in path_parts:
                idx = path_parts.index("code")
                if idx + 1 < len(path_parts):
                    project_name = path_parts[idx + 1]
                else:
                    project_name = Path(cwd).name
            else:
                project_name = Path(cwd).name

            logger.info(f"No session ID, extracted project from cwd: {project_name}")
        else:
            project_name = resolve_project_name(session_id, cwd)
            logger.info(f"Resolved project name from session: {project_name}")

        # Apply project name replacement for display and TTS
        display_project_name = apply_project_name_replacement(project_name, replacements)
        tts_project_name = get_project_pronunciation(project_name, replacements)

        cwd_name = Path(cwd).name if cwd else "unknown"

        if hook_type == "PreToolUse":
            # Claude Code sends "tool" not "tool_name"
            tool_name = hook_data.get("tool", hook_data.get("tool_name", "unknown"))

            # Only notify for truly dangerous operations
            # Skip notifications for common safe operations
            if tool_name == "Bash":
                # Claude Code sends "parameters" not "tool_input"
                command = hook_data.get("parameters", hook_data.get("tool_input", {})).get(
                    "command", ""
                )
                # Skip common safe commands
                safe_prefixes = [
                    "echo",
                    "pwd",
                    "ls",
                    "cat",
                    "head",
                    "tail",
                    "grep",
                    "find",
                    "which",
                ]
                if any(command.strip().startswith(prefix) for prefix in safe_prefixes):
                    return  # Skip notification

                # Only notify for potentially dangerous commands
                dangerous_prefixes = [
                    "rm",
                    "mv",
                    "cp",
                    "sudo",
                    "chmod",
                    "chown",
                    ">",
                    "curl",
                    "wget",
                ]
                if any(prefix in command for prefix in dangerous_prefixes):
                    event_type = "tool_activity"
                    # Extract the command and first argument for cleaner message
                    # Split only up to pipe to avoid getting arguments from piped commands
                    base_command = command.split("|")[0] if "|" in command else command
                    cmd_parts = base_command.split()
                    cmd_summary = cmd_parts[0] if cmd_parts else "command"

                    # Create natural TTS descriptions
                    target = None

                    # Special handling for curl/wget - don't extract file names from URLs
                    if cmd_summary in ["curl", "wget"]:
                        # For curl/wget, only show the domain if it's a URL
                        for part in cmd_parts[1:]:
                            if part.startswith("http://") or part.startswith("https://"):
                                # Extract just the domain
                                try:
                                    parsed = urlparse(part)
                                    target = parsed.netloc if parsed.netloc else None
                                except:
                                    pass
                                break
                            elif not part.startswith("-"):
                                # If it's a file path (not a URL), show the filename
                                if "/" not in part and "." in part:
                                    target = part
                                break
                    elif len(cmd_parts) > 1 and cmd_parts[1]:
                        # Get just the filename/target, not full path
                        potential_target = cmd_parts[1]

                        # Skip if it looks like code or complex syntax
                        if any(
                            char in potential_target
                            for char in ["(", ")", "[", "]", "{", "}", '"', "'", "|", ";"]
                        ):
                            target = None
                        elif potential_target.startswith("-"):
                            # It's a flag, try to find a real target
                            for part in cmd_parts[2:]:
                                if not part.startswith("-") and not any(
                                    char in part
                                    for char in ["(", ")", "[", "]", "{", "}", '"', "'", "|", ";"]
                                ):
                                    target = Path(part).name if "/" in part else part
                                    break
                        else:
                            target = (
                                Path(potential_target).name
                                if "/" in potential_target
                                else potential_target
                            )

                    # Generate human-friendly descriptions for TTS
                    tts_descriptions = {
                        "rm": f"removing {target}" if target else "removing files",
                        "rm -rf": f"force removing {target}" if target else "force removing files",
                        "rm -r": f"removing directory {target}" if target else "removing directory",
                        "mv": f"moving {target}" if target else "moving files",
                        "cp": f"copying {target}" if target else "copying files",
                        "sudo": "running with admin privileges",
                        "chmod": (
                            f"changing permissions on {target}"
                            if target
                            else "changing permissions"
                        ),
                        "chown": (
                            f"changing ownership of {target}" if target else "changing ownership"
                        ),
                        "curl": "fetching data",
                        "wget": "downloading file",
                    }

                    # Check for specific command patterns
                    if cmd_summary == "rm" and "-rf" in command:
                        audio_desc = tts_descriptions["rm -rf"]
                    elif cmd_summary == "rm" and "-r" in command:
                        audio_desc = tts_descriptions["rm -r"]
                    elif cmd_summary in tts_descriptions:
                        audio_desc = tts_descriptions[cmd_summary]
                    else:
                        audio_desc = f"running {cmd_summary}"

                    # Build messages
                    if target and len(target) < 50:  # Sanity check on target length
                        message = f"[{display_project_name}] Running {cmd_summary} on {target}"
                    else:
                        message = f"[{display_project_name}] Running {cmd_summary}"

                    # Natural TTS message
                    custom_tts = f"{tts_project_name}, {audio_desc}"

            # Skip most file edits unless they're system files
            elif tool_name in ["Write", "MultiEdit", "Edit"]:
                # Claude Code sends "parameters" not "tool_input"
                file_path = hook_data.get("parameters", hook_data.get("tool_input", {})).get(
                    "file_path", ""
                )
                # Only notify for system/config files
                if any(x in file_path for x in ["/etc/", "/usr/", ".env", "config", "secret"]):
                    event_type = "tool_activity"
                    file_name = Path(file_path).name

                    # More natural descriptions based on tool
                    if tool_name == "Write":
                        action_desc = "writing"
                    elif tool_name == "MultiEdit":
                        action_desc = "multi-editing"
                    else:
                        action_desc = "editing"

                    message = f"[{display_project_name}] {action_desc.capitalize()} {file_name}"
                    custom_tts = f"{tts_project_name}, {action_desc} {file_name}"

        elif hook_type == "PostToolUse":
            # Check for errors in tool response
            # Claude Code might send "response" or "tool_response"
            tool_response = hook_data.get("response", hook_data.get("tool_response", {}))
            # Claude Code sends "tool" not "tool_name"
            tool_name = hook_data.get("tool", hook_data.get("tool_name", "unknown"))

            # Debug log the tool response structure
            logger.debug(
                f"PostToolUse response for {tool_name}: {json.dumps(tool_response, indent=2) if isinstance(tool_response, dict) else tool_response}"
            )

            # Check if response indicates an error (type: "error" or has non-empty error field)
            if isinstance(tool_response, dict) and (
                tool_response.get("type") == "error"
                or (tool_response.get("error") and tool_response.get("error") != "")
            ):
                event_type = "error"
                error_msg = tool_response.get(
                    "error", tool_response.get("message", "Unknown error")
                )
                message = f"[{display_project_name}] Error in {tool_name}: {str(error_msg)[:100]}"
                custom_tts = f"{tts_project_name}, {tool_name} failed"

        elif hook_type == "Stop":
            event_type = "execution_complete"
            message = f"[{display_project_name}] Task complete"
            custom_tts = f"{tts_project_name}, task completed successfully"

        elif hook_type == "SubagentStop":
            event_type = "subagent_done"
            message = f"[{display_project_name}] Subagent finished"
            custom_tts = f"{tts_project_name}, sub agent finished"

        elif hook_type == "PreCompact":
            event_type = "compaction"
            message = "Context compaction starting"

        elif hook_type == "Notification":
            # Handle user input/confirmation needed scenarios
            notif_type = hook_data.get("notification_type", "")
            raw_message = hook_data.get("message", "")

            # Debug log to understand what triggers notifications
            logger.debug(
                f"Notification received - type: {notif_type}, message: {raw_message[:200] if raw_message else 'None'}"
            )

            if "error" in notif_type.lower():
                event_type = "error"
                message = hook_data.get("message", "An error occurred")
            elif raw_message:  # Only process if there's actually a message
                # Check if this is truly a permission/confirmation request
                permission_keywords = [
                    "permission to use",
                    "permission needed",
                    "needs your permission",
                    "confirm",
                    "approve",
                    "allow",
                ]

                if any(keyword in raw_message.lower() for keyword in permission_keywords):
                    event_type = "input_needed"
                    # Extract what Claude needs permission for
                    if "permission to use" in raw_message:
                        # Extract tool name from "Claude needs your permission to use [Tool]"
                        tool_match = re.search(r"permission to use (\w+)", raw_message)
                        if tool_match:
                            tool_requested = tool_match.group(1)
                            message = (
                                f"[{display_project_name}] Permission needed for {tool_requested}"
                            )
                            custom_tts = (
                                f"{tts_project_name}, needs permission for {tool_requested}"
                            )
                        else:
                            message = f"[{display_project_name}] {raw_message}"
                            custom_tts = f"{tts_project_name}, {raw_message}"
                    else:
                        message = f"[{display_project_name}] Input needed"
                        custom_tts = f"{tts_project_name}, input needed"
                else:
                    # Not a permission request - log it but don't notify
                    logger.debug(
                        f"Notification ignored (not a permission request): {raw_message[:100]}"
                    )
                    return  # Skip notification

        # Send notification if we have an event
        if event_type and message:
            logger.info(f"Sending notification: event_type={event_type}, message={message}")

            # Extract the actual message without the project prefix
            clean_message = message.split("] ", 1)[-1] if "] " in message else message

            # Simple and clean: project as title, message as content
            self.notify(title=display_project_name, message=clean_message)

            # Play sound if available
            sound_file = self.get_notification_sound(event_type, custom_tts or "")
            if sound_file:
                logger.info(f"Playing sound: {sound_file}")
                self.play_sound_file(sound_file)
        else:
            logger.debug(f"No notification sent: event_type={event_type}, message={message}")


def main():
    """Main notification handler entry point"""
    # Parse command-line arguments
    import argparse

    parser = argparse.ArgumentParser(description="CCNotify notification handler")
    parser.add_argument("--logging", action="store_true", help="Enable logging to file")
    args, unknown = parser.parse_known_args()

    # Load .env file if available
    try:
        env_file = BASE_DIR / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            # Re-read environment variables after loading .env
            global USE_TTS, USE_LOGGING, TTS_PROVIDER, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, ELEVENLABS_MODEL_ID, KOKORO_VOICE, KOKORO_PATH, KOKORO_SPEED
            USE_TTS = os.getenv("USE_TTS", "true").lower() == "true"
            USE_LOGGING = os.getenv("USE_LOGGING", "false").lower() == "true"
            TTS_PROVIDER = os.getenv("TTS_PROVIDER", "kokoro")
            ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
            ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
            ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_flash_v2_5")
            KOKORO_VOICE = os.getenv("KOKORO_VOICE", "af_heart")
            # KOKORO_PATH is now determined from config file
            KOKORO_SPEED = os.getenv("KOKORO_SPEED", "1.0")
    except ImportError:
        pass

    # Setup logging based on command-line flag or environment variable
    setup_logging(enable_logging=args.logging)

    handler = NotificationHandler()

    # Check if running interactively (for testing)
    if sys.stdin.isatty():
        # Test mode
        if len(unknown) > 0:
            event_type = unknown[0]
            message = unknown[1] if len(unknown) > 1 else "Test notification"
            logger.info(f"Test mode: event_type={event_type}, message={message}")
            handler.notify("Claude Code", message, event_type)
            sound = handler.get_notification_sound(event_type)
            if sound:
                handler.play_sound_file(sound)
        else:
            print("Test mode: python notify.py <event_type> [message]")
    else:
        # Read JSON from stdin
        try:
            raw_input = sys.stdin.read()
            logger.info(f"Raw input received: {raw_input}")

            hook_data = json.loads(raw_input)
            logger.info(f"Parsed hook data: {json.dumps(hook_data, indent=2)}")

            handler.handle_hook(hook_data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON input: {e}")
            logger.error(f"Raw input was: {raw_input}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error: {type(e).__name__}: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
