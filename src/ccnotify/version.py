"""Version management utilities for CCNotify."""

import re
from pathlib import Path
from typing import Optional, Tuple

try:
    from packaging import version
except ImportError:
    # Fallback version comparison if packaging is not available
    version = None


def get_package_version() -> str:
    """Get the current package version."""
    try:
        from . import __version__

        return __version__
    except ImportError:
        return "unknown"


def extract_script_version(script_path: Path) -> Optional[str]:
    """Extract version from ccnotify.py script file."""
    if not script_path.exists():
        return None

    try:
        content = script_path.read_text()
        # Look for version pattern in the script
        version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
        if version_match:
            return version_match.group(1)
    except Exception:
        pass

    return None


def compare_versions(new_version: str, current_version: str) -> int:
    """
    Compare two version strings.

    Returns:
        1 if new_version > current_version
        0 if new_version == current_version
        -1 if new_version < current_version
    """
    if new_version == "unknown" or current_version == "unknown":
        return 0

    if version is not None:
        try:
            new_v = version.parse(new_version)
            current_v = version.parse(current_version)

            if new_v > current_v:
                return 1
            elif new_v == current_v:
                return 0
            else:
                return -1
        except Exception:
            pass

    # Fallback to string comparison
    if new_version == current_version:
        return 0
    return 1 if new_version > current_version else -1


def is_newer_version(new_version: str, current_version: str) -> bool:
    """Check if new_version is newer than current_version."""
    return compare_versions(new_version, current_version) == 1


def is_same_version(new_version: str, current_version: str) -> bool:
    """Check if versions are the same."""
    return compare_versions(new_version, current_version) == 0


def format_version_info(current: Optional[str], available: Optional[str]) -> str:
    """Format version information for display."""
    if not current:
        return f"Not installed → {available or 'unknown'}"

    if not available:
        return f"Installed: {current}"

    if is_newer_version(available, current):
        return f"{current} → {available} (update available)"
    elif is_same_version(current, available):
        return f"{current} (up to date)"
    else:
        return f"{current} (newer than available {available})"


def parse_config_version(config_data: dict) -> str:
    """Extract config version from configuration data."""
    return config_data.get("config_version", "1.0")


def needs_config_migration(current_config_version: str, target_version: str = "1.0") -> bool:
    """Check if config format needs migration."""
    if version is not None:
        try:
            return version.parse(current_config_version) < version.parse(target_version)
        except Exception:
            pass

    # Fallback comparison if packaging is not available
    return current_config_version != target_version


def embed_version_in_script(script_content: str, version_string: str) -> str:
    """Embed version information in generated script."""
    # Add version constant at the top of the script
    version_line = f'__version__ = "{version_string}"\n'

    # Find the appropriate place to insert the version
    # Look for imports section and add after it
    lines = script_content.split("\n")
    insert_index = 0

    # Find last import or the shebang line
    for i, line in enumerate(lines):
        if line.startswith("#!") or line.startswith("import ") or line.startswith("from "):
            insert_index = i + 1
        elif line.strip() == "" and insert_index > 0:
            # Found empty line after imports
            break

    # Insert version line
    lines.insert(insert_index, version_line)

    return "\n".join(lines)


def get_version_summary() -> dict:
    """Get a summary of all version information."""
    from .installer.detector import InstallationDetector

    detector = InstallationDetector()
    status = detector.check_existing_installation()
    package_version = get_package_version()

    return {
        "package_version": package_version,
        "installed_script_version": status.script_version,
        "config_version": status.config_version,
        "update_available": is_newer_version(package_version, status.script_version or "0.0.0"),
        "migration_needed": needs_config_migration(status.config_version or "0.0.0"),
    }
