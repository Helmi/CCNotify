"""Update management and version comparison for CCNotify."""

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any
from packaging import version

from .detector import InstallationDetector, InstallationStatus
from ..config import get_claude_config_dir


@dataclass
class UpdateInfo:
    """Information about available updates."""

    script_update_available: bool = False
    current_script_version: Optional[str] = None
    available_script_version: Optional[str] = None
    config_migration_needed: bool = False
    model_update_available: bool = False
    recommended_actions: List[str] = None

    def __post_init__(self):
        if self.recommended_actions is None:
            self.recommended_actions = []


class UpdateManager:
    """Manages updates for CCNotify installation."""

    def __init__(self):
        self.detector = InstallationDetector()
        self.claude_dir = get_claude_config_dir()
        self.ccnotify_dir = self.claude_dir / "ccnotify"

    def check_for_updates(self, installation_status: InstallationStatus) -> UpdateInfo:
        """Check what updates are available for existing installation."""
        update_info = UpdateInfo()

        # Get current package version
        try:
            from .. import __version__ as package_version

            update_info.available_script_version = package_version
        except ImportError:
            # Fallback if we can't import version
            update_info.available_script_version = "unknown"

        # Compare script versions
        if installation_status.script_version:
            update_info.current_script_version = installation_status.script_version

            if self._is_newer_version(
                update_info.available_script_version, installation_status.script_version
            ):
                update_info.script_update_available = True
                update_info.recommended_actions.append(
                    f"Update script from v{installation_status.script_version} to v{update_info.available_script_version}"
                )

        # Check if config needs migration
        if installation_status.config_version:
            if self._needs_config_migration(installation_status.config_version):
                update_info.config_migration_needed = True
                update_info.recommended_actions.append("Migrate configuration to newer format")

        # Check model updates (for Kokoro provider)
        if installation_status.tts_provider == "kokoro":
            if self._check_model_updates():
                update_info.model_update_available = True
                update_info.recommended_actions.append("Update Kokoro TTS models")

        return update_info

    def _is_newer_version(self, new_version: str, current_version: str) -> bool:
        """Compare versions using semantic versioning."""
        if new_version == "unknown" or current_version == "unknown":
            return False

        try:
            return version.parse(new_version) > version.parse(current_version)
        except Exception:
            # Fallback to string comparison if version parsing fails
            return new_version != current_version

    def _needs_config_migration(self, current_config_version: str) -> bool:
        """Check if config format needs migration."""
        # Define config version migrations here
        CURRENT_CONFIG_VERSION = "1.0"

        try:
            return version.parse(current_config_version) < version.parse(CURRENT_CONFIG_VERSION)
        except Exception:
            # If we can't parse versions, assume migration is needed
            return True

    def _check_model_updates(self) -> bool:
        """Check if TTS model updates are available."""
        # For now, return False - this would check remote model versions
        # in a real implementation
        return False

    def create_backup(self, backup_suffix: str = ".backup") -> Dict[str, Path]:
        """Create backup of current installation before update."""
        backups = {}

        if self.ccnotify_dir.exists():
            backup_dir = self.ccnotify_dir.with_suffix(backup_suffix)

            # Remove existing backup if it exists
            if backup_dir.exists():
                shutil.rmtree(backup_dir)

            # Create new backup
            shutil.copytree(self.ccnotify_dir, backup_dir)
            backups["ccnotify_dir"] = backup_dir

        # Backup Claude settings
        settings_file = self.claude_dir / "settings.json"
        if settings_file.exists():
            backup_settings = settings_file.with_suffix(f".json{backup_suffix}")
            shutil.copy2(settings_file, backup_settings)
            backups["settings"] = backup_settings

        return backups

    def restore_from_backup(self, backup_paths: Dict[str, Path]) -> bool:
        """Restore from backup in case of failed update."""
        try:
            # Restore ccnotify directory
            if "ccnotify_dir" in backup_paths and backup_paths["ccnotify_dir"].exists():
                if self.ccnotify_dir.exists():
                    shutil.rmtree(self.ccnotify_dir)
                shutil.copytree(backup_paths["ccnotify_dir"], self.ccnotify_dir)

            # Restore settings
            if "settings" in backup_paths and backup_paths["settings"].exists():
                settings_file = self.claude_dir / "settings.json"
                shutil.copy2(backup_paths["settings"], settings_file)

            return True
        except Exception:
            return False

    def cleanup_backups(self, backup_paths: Dict[str, Path]) -> None:
        """Clean up backup files after successful update."""
        for backup_path in backup_paths.values():
            try:
                if backup_path.is_dir():
                    shutil.rmtree(backup_path)
                else:
                    backup_path.unlink()
            except Exception:
                pass  # Ignore cleanup errors

    def migrate_legacy_installation(self) -> bool:
        """Migrate from legacy ~/.claude/hooks/ structure to ~/.claude/ccnotify/."""
        legacy_hooks_dir = self.claude_dir / "hooks"

        if not legacy_hooks_dir.exists():
            return True  # Nothing to migrate

        if self.ccnotify_dir.exists():
            return True  # Already migrated

        try:
            # Create ccnotify directory
            self.ccnotify_dir.mkdir(exist_ok=True)

            # Migrate files
            for item in legacy_hooks_dir.iterdir():
                if item.is_file():
                    target = self.ccnotify_dir / item.name
                    shutil.copy2(item, target)

            # Update Claude settings to point to new location
            self._update_hooks_path_in_settings()

            return True
        except Exception:
            return False

    def _update_hooks_path_in_settings(self) -> bool:
        """Update Claude settings.json to use new ccnotify path."""
        settings_file = self.claude_dir / "settings.json"

        if not settings_file.exists():
            return True

        try:
            with open(settings_file) as f:
                settings = json.load(f)

            # Update hook commands to use new path
            hooks = settings.get("hooks", {})
            updated = False

            for hook_name, hook_config in hooks.items():
                if isinstance(hook_config, dict):
                    command = hook_config.get("command", "")
                    if "/.claude/hooks/" in command:
                        new_command = command.replace("/.claude/hooks/", "/.claude/ccnotify/")
                        hook_config["command"] = new_command
                        updated = True

            if updated:
                with open(settings_file, "w") as f:
                    json.dump(settings, f, indent=2)

            return True
        except Exception:
            return False

    def update_script_only(self, preserve_config: bool = True) -> bool:
        """Update only the ccnotify.py script, preserving configuration."""
        try:
            # Backup configuration if requested
            config_backup = None
            if preserve_config:
                config_file = self.ccnotify_dir / "config.json"
                if config_file.exists():
                    config_backup = config_file.read_text()

            # Generate new script with updated template
            from ..cli import get_notify_template

            script_content = get_notify_template()

            # Update the script file
            script_file = self.ccnotify_dir / "ccnotify.py"
            script_file.write_text(script_content)
            script_file.chmod(0o755)

            # Restore configuration
            if config_backup and preserve_config:
                config_file = self.ccnotify_dir / "config.json"
                config_file.write_text(config_backup)

            return True
        except Exception:
            return False

    def get_current_package_version(self) -> str:
        """Get the current package version."""
        try:
            from .. import __version__

            return __version__
        except ImportError:
            return "unknown"
