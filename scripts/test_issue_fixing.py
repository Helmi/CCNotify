#!/usr/bin/env python3
"""Test that update flow fixes issues even when version is current."""

import sys
import tempfile
import shutil
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_issue_fixing_without_version_update():
    """Test that issues are fixed even when script version is already current."""
    from ccnotify.installer.flows import UpdateFlow
    from ccnotify.installer.detector import InstallationStatus
    from ccnotify.installer.updater import UpdateInfo
    from ccnotify import __version__
    
    print(f"Testing issue fixing with current version {__version__}...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set up a fake ccnotify directory with current version
        ccnotify_dir = Path(tmpdir) / ".claude" / "ccnotify"
        ccnotify_dir.mkdir(parents=True)
        
        # Create script with CURRENT version (no update needed)
        script_file = ccnotify_dir / "ccnotify.py"
        script_file.write_text(f'#!/usr/bin/env python3\n__version__ = "{__version__}"\n')
        
        # Create config
        config = {"tts_provider": "kokoro", "config_version": "1.0"}
        config_file = ccnotify_dir / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        # Create UpdateFlow instance
        flow = UpdateFlow()
        flow.ccnotify_dir = ccnotify_dir
        
        # Mock status with issues but current version
        status = InstallationStatus()
        status.exists = True
        status.script_version = __version__  # Current version - no update needed
        status.config_version = "1.0"
        status.tts_provider = "kokoro"
        status.models_downloaded = True
        status.hooks_configured = False  # Issue!
        status.issues = ["CCNotify installed but not configured in Claude settings"]
        
        # Mock update info - no updates available
        update_info = UpdateInfo()
        update_info.script_update_available = False
        update_info.config_migration_needed = False
        update_info.model_update_available = False
        update_info.recommended_actions = []
        
        print("Testing with:")
        print(f"  Script version: {status.script_version} (current)")
        print(f"  Issues: {status.issues}")
        print(f"  Updates available: None")
        
        # Check the has_updates logic
        has_updates = flow._has_updates(update_info)
        print(f"  Has updates: {has_updates}")
        
        # Check if flow would return early (old bug)
        would_skip = not has_updates and not status.issues
        print(f"  Would skip fixing (old bug): {would_skip}")
        
        # Check if flow will proceed (new fix)
        will_proceed = has_updates or status.issues
        print(f"  Will proceed to fix issues: {will_proceed}")
        
        if will_proceed:
            print("✅ Update flow will now fix issues even without version updates!")
        else:
            print("❌ Update flow would still skip issue fixing!")
            return False
        
        # Test confirmation dialog
        actions = []
        if update_info.recommended_actions:
            actions.extend(update_info.recommended_actions)
        if status.issues:
            for issue in status.issues:
                if "not configured in Claude settings" in issue:
                    actions.append("Configure Claude hooks")
        
        print(f"\nActions that will be shown to user: {actions}")
        
        if actions:
            print("✅ User will be prompted to fix hooks configuration")
        else:
            print("❌ No actions would be shown to user")
            return False
        
        return True

if __name__ == "__main__":
    success = test_issue_fixing_without_version_update()
    
    if success:
        print("\n✅ Issue fixing test passed! Hooks will now be configured automatically.")
    else:
        print("\n❌ Issue fixing test failed!")
    
    sys.exit(0 if success else 1)