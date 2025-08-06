#!/usr/bin/env python3
"""
Fix duplicate CCNotify hooks in Claude settings.json
Run this if you have multiple duplicate hooks from earlier versions.
"""

import json
import shutil
from pathlib import Path
import sys

def fix_duplicate_hooks():
    """Remove duplicate CCNotify hooks from settings.json."""
    
    settings_file = Path.home() / ".claude" / "settings.json"
    
    if not settings_file.exists():
        print("No settings.json found. Nothing to fix.")
        return 0
    
    # Backup first
    backup_file = settings_file.with_suffix('.json.before-dedup.bak')
    shutil.copy2(settings_file, backup_file)
    print(f"Created backup: {backup_file}")
    
    # Load settings
    with open(settings_file) as f:
        settings = json.load(f)
    
    if "hooks" not in settings:
        print("No hooks configured. Nothing to fix.")
        return 0
    
    # Track what we fixed
    fixed_count = 0
    
    # Process each hook type
    for hook_type in ["PreToolUse", "PostToolUse", "Stop", "SubagentStop", "Notification"]:
        if hook_type not in settings["hooks"]:
            continue
        
        original_count = len(settings["hooks"][hook_type])
        
        # Find and keep only one ccnotify hook
        ccnotify_hook = None
        other_hooks = []
        
        for entry in settings["hooks"][hook_type]:
            if isinstance(entry, dict) and "hooks" in entry:
                # Check if this is a ccnotify hook
                is_ccnotify = False
                for hook in entry.get("hooks", []):
                    if isinstance(hook, dict):
                        command = hook.get("command", "")
                        if "ccnotify.py" in command:
                            is_ccnotify = True
                            if not ccnotify_hook:  # Keep first one found
                                ccnotify_hook = entry
                            break
                
                if not is_ccnotify:
                    other_hooks.append(entry)
            else:
                # Keep non-standard entries
                other_hooks.append(entry)
        
        # Rebuild the hook list
        new_hooks = other_hooks
        if ccnotify_hook:
            new_hooks.append(ccnotify_hook)
        
        settings["hooks"][hook_type] = new_hooks
        
        new_count = len(new_hooks)
        if new_count < original_count:
            removed = original_count - new_count
            print(f"  {hook_type}: Removed {removed} duplicate(s) ({original_count} → {new_count})")
            fixed_count += removed
    
    if fixed_count > 0:
        # Save fixed settings
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        
        print(f"\n✅ Fixed! Removed {fixed_count} duplicate hook(s).")
        print(f"   Backup saved to: {backup_file}")
        print("\nRestart Claude Code for changes to take effect.")
    else:
        print("\n✅ No duplicates found. Your hooks are already clean!")
    
    return 0

if __name__ == "__main__":
    sys.exit(fix_duplicate_hooks())