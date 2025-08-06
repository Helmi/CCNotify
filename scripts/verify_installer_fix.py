#!/usr/bin/env python3
"""
Verify the installer fix works correctly
"""

import subprocess
import sys
import tempfile
import os
import json
from pathlib import Path

def run_test():
    """Run comprehensive installer test"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        print("🧪 CCNotify Installer Fix Verification")
        print("=" * 50)
        
        # Create venv
        venv_dir = Path(tmpdir) / "venv"
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
        
        # Paths
        if sys.platform == "win32":
            python = venv_dir / "Scripts" / "python.exe"
            pip = venv_dir / "Scripts" / "pip.exe"
        else:
            python = venv_dir / "bin" / "python"
            pip = venv_dir / "bin" / "pip"
        
        # Install package from TestPyPI
        print("\n📦 Installing ccnotify v0.1.3 from TestPyPI...")
        result = subprocess.run([
            str(pip), "install", 
            "--index-url", "https://test.pypi.org/simple/",
            "--extra-index-url", "https://pypi.org/simple/",
            "ccnotify==0.1.3"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Installation failed: {result.stderr}")
            return False
        
        print("✅ Package installed successfully")
        
        # Create test home
        test_home = Path(tmpdir) / "home"
        test_home.mkdir()
        (test_home / ".claude").mkdir()
        
        # Create settings.json
        settings = {
            "version": "1.0",
            "hooks": {
                "preToolUse": [],
                "postToolUse": []
            }
        }
        
        settings_file = test_home / ".claude" / "settings.json"
        settings_file.write_text(json.dumps(settings, indent=2))
        
        # Set environment
        env = os.environ.copy()
        env["HOME"] = str(test_home)
        
        # Test the installer
        print(f"\n🏠 Test HOME: {test_home}")
        print("\n🚀 Running installer...")
        
        test_script = """
import os
os.environ['HOME'] = os.environ.get('TEST_HOME', os.environ['HOME'])

from ccnotify.cli import execute_install_command

# Run installer in quiet mode
success = execute_install_command(quiet=True, force=True)
print(f"Installation result: {success}")

# Check what was created
ccnotify_dir = os.path.join(os.environ['HOME'], '.claude', 'ccnotify')
if os.path.exists(ccnotify_dir):
    print(f"✅ Created directory: {ccnotify_dir}")
    for item in sorted(os.listdir(ccnotify_dir)):
        print(f"   - {item}")
        
    # Check config
    config_file = os.path.join(ccnotify_dir, 'config.json')
    if os.path.exists(config_file):
        import json
        with open(config_file) as f:
            config = json.load(f)
        print(f"\\nConfig contents:")
        print(f"   TTS Provider: {config.get('tts_provider', 'N/A')}")
else:
    print("❌ Installation directory not created")
"""
        
        env["TEST_HOME"] = str(test_home)
        
        result = subprocess.run(
            [str(python), "-c", test_script],
            env=env,
            capture_output=True,
            text=True
        )
        
        print("\nOutput:")
        print(result.stdout)
        
        if result.stderr:
            print("\nErrors:")
            print(result.stderr)
        
        # Check if there were any errors about KokoroProvider
        if "PosixPath" in result.stderr or "object has no attribute 'get'" in result.stderr:
            print("\n❌ The KokoroProvider error still exists!")
            return False
        
        if result.returncode == 0 and "Installation result: True" in result.stdout:
            print("\n✅ Installer completed successfully!")
            print("✅ No KokoroProvider errors detected!")
            return True
        else:
            print("\n❌ Installer failed")
            return False

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)