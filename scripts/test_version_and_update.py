#!/usr/bin/env python3
"""Test version management and update flow."""

import sys
import tempfile
import shutil
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_script_update():
    """Test that script update actually updates the script with correct version."""
    from ccnotify.installer.updater import UpdateManager
    from ccnotify.cli import get_notify_template
    from ccnotify import __version__
    
    print(f"Testing script update with version {__version__}...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set up a fake ccnotify directory
        ccnotify_dir = Path(tmpdir) / ".claude" / "ccnotify"
        ccnotify_dir.mkdir(parents=True)
        
        # Create an old script
        old_script = ccnotify_dir / "ccnotify.py"
        old_script.write_text('#!/usr/bin/env python3\n__version__ = "0.1.3"\nprint("old")')
        
        # Create a config
        config = {"tts_provider": "kokoro", "config_version": "1.0"}
        config_file = ccnotify_dir / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        # Create updater and update script
        updater = UpdateManager()
        updater.ccnotify_dir = ccnotify_dir
        
        print("Updating script...")
        success = updater.update_script_only(preserve_config=True)
        
        if not success:
            print("❌ Script update failed")
            return False
        
        # Check the updated script
        updated_content = old_script.read_text()
        
        # Check version is embedded correctly
        if f'__version__ = "{__version__}"' in updated_content:
            print(f"✅ Version {__version__} correctly embedded in script")
        else:
            print(f"❌ Version not correctly embedded. Looking for: __version__ = \"{__version__}\"")
            print("Script content preview:")
            print(updated_content[:500])
            return False
        
        # Check config was preserved
        if config_file.exists():
            with open(config_file) as f:
                preserved_config = json.load(f)
            if preserved_config == config:
                print("✅ Configuration preserved during update")
            else:
                print("❌ Configuration changed during update")
                return False
        else:
            print("❌ Configuration file lost during update")
            return False
        
        return True

def test_version_consistency():
    """Test that all version sources are consistent."""
    from ccnotify import __version__ as init_version
    from ccnotify.version import get_package_version
    from ccnotify.cli import get_notify_template
    
    print("\nChecking version consistency...")
    
    # Check __init__.py version
    print(f"__init__.py version: {init_version}")
    
    # Check get_package_version
    pkg_version = get_package_version()
    print(f"get_package_version: {pkg_version}")
    
    if init_version != pkg_version:
        print("❌ Version mismatch between __init__.py and get_package_version")
        return False
    
    # Check template generation
    template = get_notify_template()
    if f'__version__ = "{init_version}"' in template:
        print(f"✅ Template correctly embeds version {init_version}")
    else:
        print("❌ Template doesn't correctly embed version")
        # Show what's in the template
        for line in template.split('\n'):
            if '__version__' in line:
                print(f"  Found: {line}")
        return False
    
    print("✅ All version sources are consistent")
    return True

if __name__ == "__main__":
    success = True
    
    if not test_version_consistency():
        success = False
    
    if not test_script_update():
        success = False
    
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed")
    
    sys.exit(0 if success else 1)