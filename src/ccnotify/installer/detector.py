"""Installation detection and status checking for CCNotify."""

import json
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any
import re

from ..config import get_claude_config_dir


@dataclass
class InstallationStatus:
    """Status of an existing CCNotify installation."""

    exists: bool = False
    script_version: Optional[str] = None
    config_version: Optional[str] = None
    tts_provider: Optional[str] = None
    models_downloaded: bool = False
    hooks_configured: bool = False
    legacy_hooks_dir: bool = False
    issues: List[str] = None

    def __post_init__(self):
        if self.issues is None:
            self.issues = []


@dataclass
class ConfigStatus:
    """Status of CCNotify configuration."""

    exists: bool = False
    valid: bool = False
    provider: Optional[str] = None
    version: Optional[str] = None
    issues: List[str] = None

    def __post_init__(self):
        if self.issues is None:
            self.issues = []


@dataclass
class ModelStatus:
    """Status of TTS models."""

    provider: Optional[str] = None
    kokoro_downloaded: bool = False
    kokoro_models_count: int = 0
    elevenlabs_configured: bool = False
    issues: List[str] = None

    def __post_init__(self):
        if self.issues is None:
            self.issues = []


class InstallationDetector:
    """Detects and analyzes existing CCNotify installations."""

    def __init__(self):
        self.claude_dir = get_claude_config_dir()
        self.ccnotify_dir = self.claude_dir / "ccnotify"
        self.legacy_hooks_dir = self.claude_dir / "hooks"
        self.settings_file = self.claude_dir / "settings.json"

    def check_existing_installation(self) -> InstallationStatus:
        """Check for existing CCNotify installation and return comprehensive status."""
        status = InstallationStatus()

        # Check if ccnotify directory exists
        if self.ccnotify_dir.exists():
            status.exists = True
            status.script_version = self._get_script_version()
            config_status = self.get_config_status()
            status.config_version = config_status.version
            status.tts_provider = config_status.provider

            # Check hooks configuration
            status.hooks_configured = self._check_hooks_configured()

            # Check models
            model_status = self.get_model_status()
            status.models_downloaded = (
                model_status.kokoro_downloaded or model_status.elevenlabs_configured
            )

            # Collect issues
            status.issues.extend(config_status.issues)
            status.issues.extend(model_status.issues)

        # Check for legacy hooks directory
        if self.legacy_hooks_dir.exists():
            status.legacy_hooks_dir = True
            if not status.exists:
                status.issues.append(
                    "Found legacy installation in ~/.claude/hooks/ - needs migration"
                )

        # Additional validation
        if status.exists and not status.hooks_configured:
            status.issues.append("CCNotify installed but not configured in Claude settings")

        return status

    def get_installed_version(self) -> Optional[str]:
        """Extract version from installed ccnotify.py script."""
        return self._get_script_version()

    def _get_script_version(self) -> Optional[str]:
        """Get version from ccnotify.py script file."""
        script_file = self.ccnotify_dir / "ccnotify.py"
        if not script_file.exists():
            return None

        try:
            content = script_file.read_text()
            # Look for version pattern in the script
            version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
            if version_match:
                return version_match.group(1)
        except Exception:
            pass

        return None

    def get_config_status(self) -> ConfigStatus:
        """Analyze configuration file status."""
        status = ConfigStatus()
        config_file = self.ccnotify_dir / "config.json"

        if not config_file.exists():
            return status

        status.exists = True

        try:
            with open(config_file) as f:
                config = json.load(f)

            status.valid = True
            status.provider = config.get("tts_provider")
            status.version = config.get("config_version", "1.0")

            # Validate required fields
            required_fields = ["tts_provider"]
            for field in required_fields:
                if field not in config:
                    status.issues.append(f"Missing required config field: {field}")
                    status.valid = False

            # Provider-specific validation
            if status.provider == "elevenlabs":
                if not config.get("elevenlabs_api_key"):
                    status.issues.append("ElevenLabs provider selected but no API key configured")

        except json.JSONDecodeError:
            status.issues.append("Config file exists but contains invalid JSON")
        except Exception as e:
            status.issues.append(f"Error reading config file: {str(e)}")

        return status

    def get_model_status(self) -> ModelStatus:
        """Check TTS model download status."""
        status = ModelStatus()
        config_status = self.get_config_status()

        if not config_status.exists:
            return status

        status.provider = config_status.provider

        if status.provider == "kokoro":
            # Check for Kokoro models
            models_dir = self.ccnotify_dir / "models"
            if models_dir.exists():
                onnx_files = list(models_dir.glob("*.onnx"))
                status.kokoro_models_count = len(onnx_files)
                status.kokoro_downloaded = len(onnx_files) > 0

                if status.kokoro_models_count == 0:
                    status.issues.append("Kokoro provider selected but no models downloaded")
            else:
                status.issues.append("Kokoro provider selected but models directory missing")

        elif status.provider == "elevenlabs":
            # Check ElevenLabs configuration
            try:
                with open(self.ccnotify_dir / "config.json") as f:
                    config = json.load(f)

                if config.get("elevenlabs_api_key"):
                    status.elevenlabs_configured = True
                else:
                    status.issues.append("ElevenLabs provider selected but no API key configured")

            except Exception:
                status.issues.append("Could not verify ElevenLabs configuration")

        return status

    def _check_hooks_configured(self) -> bool:
        """Check if CCNotify hooks are configured in Claude settings."""
        if not self.settings_file.exists():
            return False

        try:
            with open(self.settings_file) as f:
                settings = json.load(f)

            hooks = settings.get("hooks", {})

            # Look for ccnotify.py in any hook configuration
            # Structure: {"hooks": {"PreToolUse": [{"matcher": ".*", "hooks": [{"command": "..."}]}]}}
            for hook_name, hook_list in hooks.items():
                if isinstance(hook_list, list):
                    for entry in hook_list:
                        if isinstance(entry, dict) and "hooks" in entry:
                            # Check the nested hooks array
                            for hook in entry.get("hooks", []):
                                if isinstance(hook, dict):
                                    command = hook.get("command", "")
                                    if "ccnotify.py" in command:
                                        return True

        except Exception:
            pass

        return False

    def get_platform_info(self) -> Dict[str, str]:
        """Get platform information."""
        return {
            "system": platform.system(),
            "platform": platform.platform(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
        }

    def needs_migration(self) -> bool:
        """Check if installation needs migration from legacy structure."""
        return self.legacy_hooks_dir.exists() and not self.ccnotify_dir.exists()

    def get_migration_info(self) -> Dict[str, Any]:
        """Get information about what needs to be migrated."""
        if not self.needs_migration():
            return {}

        info = {
            "legacy_dir": str(self.legacy_hooks_dir),
            "target_dir": str(self.ccnotify_dir),
            "files_to_migrate": [],
        }

        # Check for files that need migration
        if self.legacy_hooks_dir.exists():
            for item in self.legacy_hooks_dir.iterdir():
                if item.is_file():
                    info["files_to_migrate"].append(item.name)

        return info
