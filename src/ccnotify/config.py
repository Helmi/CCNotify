#!/usr/bin/env python3
"""
CCNotify Configuration Management
Handles configuration directories and files
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional


def get_config_dir() -> Path:
    """Get the ccnotify configuration directory"""
    if sys.platform == "darwin":  # macOS
        config_dir = Path.home() / "Library" / "Application Support" / "ccnotify"
    elif sys.platform == "linux":  # Linux
        config_dir = Path.home() / ".config" / "ccnotify"
    elif sys.platform == "win32":  # Windows
        config_dir = Path.home() / "AppData" / "Local" / "ccnotify"
    else:
        # Fallback for other platforms
        config_dir = Path.home() / ".ccnotify"

    return config_dir


def get_cache_dir() -> Path:
    """Get the ccnotify cache directory"""
    if sys.platform == "darwin":  # macOS
        cache_dir = Path.home() / "Library" / "Caches" / "ccnotify"
    elif sys.platform == "linux":  # Linux
        cache_dir = Path.home() / ".cache" / "ccnotify"
    elif sys.platform == "win32":  # Windows
        cache_dir = Path.home() / "AppData" / "Local" / "ccnotify" / "cache"
    else:
        # Fallback for other platforms
        cache_dir = Path.home() / ".ccnotify" / "cache"

    return cache_dir


def get_models_dir() -> Path:
    """Get the models directory"""
    return get_config_dir() / "models"


def ensure_config_dirs() -> bool:
    """Create configuration directories if they don't exist"""
    try:
        config_dir = get_config_dir()
        cache_dir = get_cache_dir()
        models_dir = get_models_dir()

        config_dir.mkdir(parents=True, exist_ok=True)
        cache_dir.mkdir(parents=True, exist_ok=True)
        models_dir.mkdir(parents=True, exist_ok=True)

        return True
    except Exception as e:
        print(f"❌ Failed to create config directories: {e}")
        return False


def get_default_config() -> Dict[str, Any]:
    """Get default configuration"""
    return {
        "tts": {
            "provider": "kokoro",
            "cache_enabled": True,
            "cache_dir": str(get_cache_dir()),
        },
        "kokoro": {"models_dir": str(get_models_dir()), "voice": "af_heart", "speed": "1.0"},
        "elevenlabs": {
            "voice_id": "21m00Tcm4TlvDq8ikWAM",
            "model_id": "eleven_flash_v2_5",
            "stability": 0.5,
            "similarity_boost": 0.5,
        },
        "notifications": {"enabled": True, "sound_enabled": True, "logging_enabled": False},
        "replacements": {"enabled": True, "auto_add_projects": True},
    }


def load_config() -> Dict[str, Any]:
    """Load configuration from file"""
    config_file = get_config_dir() / "config.json"

    if not config_file.exists():
        # Create default config
        config = get_default_config()
        save_config(config)
        return config

    try:
        with open(config_file, "r") as f:
            config = json.load(f)

        # Merge with defaults to ensure all keys exist
        default_config = get_default_config()
        merged_config = merge_configs(default_config, config)

        return merged_config

    except Exception as e:
        print(f"⚠️  Failed to load config: {e}")
        print("Using default configuration")
        return get_default_config()


def save_config(config: Dict[str, Any]) -> bool:
    """Save configuration to file"""
    try:
        ensure_config_dirs()
        config_file = get_config_dir() / "config.json"

        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

        return True

    except Exception as e:
        print(f"❌ Failed to save config: {e}")
        return False


def merge_configs(default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    """Merge user config with default config"""
    merged = default.copy()

    for key, value in user.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key].update(value)
        else:
            merged[key] = value

    return merged


def get_claude_config_dir() -> Path:
    """Get the Claude configuration directory (~/.claude)"""
    return Path.home() / ".claude"


def get_claude_profile_dir() -> Optional[Path]:
    """Find Claude Code profile directory"""
    possible_locations = [
        Path.home() / ".claude",
        Path.home() / ".config" / "claude",
    ]

    # Add platform-specific locations
    if sys.platform == "darwin":  # macOS
        possible_locations.extend(
            [
                Path.home() / "Library" / "Application Support" / "Claude",
                Path.home() / "Library" / "Preferences" / "Claude",
            ]
        )
    elif sys.platform == "win32":  # Windows
        possible_locations.extend(
            [
                Path.home() / "AppData" / "Roaming" / "Claude",
                Path.home() / "AppData" / "Local" / "Claude",
            ]
        )

    for location in possible_locations:
        if location.exists() and location.is_dir():
            return location

    return None


def list_claude_projects() -> Dict[str, Path]:
    """List Claude Code projects"""
    profile_dir = get_claude_profile_dir()
    if not profile_dir:
        return {}

    projects_dir = profile_dir / "projects"
    if not projects_dir.exists():
        return {}

    projects = {}
    for project_file in projects_dir.glob("*.json"):
        try:
            with open(project_file, "r") as f:
                project_data = json.load(f)

            project_name = project_data.get("name", project_file.stem)
            project_path = Path(project_data.get("path", ""))

            if project_path.exists():
                projects[project_name] = project_path

        except Exception as e:
            print(f"⚠️  Could not read project file {project_file}: {e}")

    return projects


def init_config() -> bool:
    """Initialize configuration system"""
    print("🔧 Initializing ccnotify configuration...")

    if not ensure_config_dirs():
        return False

    config = load_config()

    print(f"✅ Configuration directory: {get_config_dir()}")
    print(f"✅ Cache directory: {get_cache_dir()}")
    print(f"✅ Models directory: {get_models_dir()}")

    # Check for Claude profile
    claude_profile = get_claude_profile_dir()
    if claude_profile:
        print(f"✅ Found Claude profile: {claude_profile}")
    else:
        print("⚠️  Could not find Claude Code profile directory")

    return True


if __name__ == "__main__":
    init_config()
