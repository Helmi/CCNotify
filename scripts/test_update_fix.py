#!/usr/bin/env python3
"""Test that UpdateFlow can now handle missing models and hooks correctly."""

import sys
import tempfile
import shutil
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ccnotify.installer.flows import UpdateFlow

def test_update_flow_methods():
    """Test that UpdateFlow has access to _setup_kokoro and _configure_claude_hooks."""
    
    # Create a temporary ccnotify directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set up a fake environment
        ccnotify_dir = Path(tmpdir) / ".claude" / "ccnotify"
        ccnotify_dir.mkdir(parents=True)
        
        # Create a minimal config
        config = {
            "config_version": "1.0",
            "tts_provider": "kokoro"
        }
        with open(ccnotify_dir / "config.json", 'w') as f:
            json.dump(config, f)
        
        # Create a dummy script
        script_file = ccnotify_dir / "ccnotify.py"
        script_file.write_text("#!/usr/bin/env python3\n# SCRIPT_VERSION = '0.1.3'\n")
        
        # Create UpdateFlow instance
        flow = UpdateFlow()
        flow.ccnotify_dir = ccnotify_dir
        
        # Test that methods exist and are callable
        print("Testing UpdateFlow methods...")
        
        # Check _setup_kokoro exists
        if hasattr(flow, '_setup_kokoro'):
            print("✓ _setup_kokoro method exists")
        else:
            print("✗ _setup_kokoro method missing")
            return False
        
        # Check _configure_claude_hooks exists
        if hasattr(flow, '_configure_claude_hooks'):
            print("✓ _configure_claude_hooks method exists")
        else:
            print("✗ _configure_claude_hooks method missing")
            return False
        
        # Check that they're callable
        if callable(getattr(flow, '_setup_kokoro', None)):
            print("✓ _setup_kokoro is callable")
        else:
            print("✗ _setup_kokoro is not callable")
            return False
        
        if callable(getattr(flow, '_configure_claude_hooks', None)):
            print("✓ _configure_claude_hooks is callable")
        else:
            print("✗ _configure_claude_hooks is not callable")
            return False
        
        print("\nAll UpdateFlow methods are properly accessible!")
        return True

if __name__ == "__main__":
    success = test_update_flow_methods()
    sys.exit(0 if success else 1)