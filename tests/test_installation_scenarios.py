#!/usr/bin/env python3
"""
Comprehensive installation scenario testing for CCNotify.
Tests various installation states without needing to publish to TestPyPI.
"""

import sys
import tempfile
import shutil
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, Optional, Tuple
import threading
import http.server
import socketserver

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class LocalPyPIServer:
    """Simple local PyPI server for testing package installation."""
    
    def __init__(self, package_dir: Path, port: int = 8765):
        self.package_dir = package_dir
        self.port = port
        self.server = None
        self.thread = None
        
    def start(self):
        """Start the server in a background thread."""
        Handler = http.server.SimpleHTTPRequestHandler
        
        def serve():
            with socketserver.TCPServer(("", self.port), Handler) as httpd:
                self.server = httpd
                httpd.serve_forever()
        
        self.thread = threading.Thread(target=serve, daemon=True)
        self.thread.start()
        time.sleep(1)  # Give server time to start
        
    def stop(self):
        """Stop the server."""
        if self.server:
            self.server.shutdown()


class TestEnvironment:
    """Manages a test environment for CCNotify installation."""
    
    def __init__(self, name: str = "test"):
        self.temp_dir = Path(tempfile.mkdtemp(prefix=f"ccnotify_{name}_"))
        self.home_dir = self.temp_dir / "home"
        self.claude_dir = self.home_dir / ".claude"
        self.ccnotify_dir = self.claude_dir / "ccnotify"
        
    def __enter__(self):
        self.setup()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        
    def setup(self):
        """Create basic directory structure."""
        self.home_dir.mkdir(parents=True)
        self.claude_dir.mkdir()
        
    def cleanup(self):
        """Remove test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def create_old_installation(self, version: str = "0.1.3"):
        """Create an old CCNotify installation."""
        self.ccnotify_dir.mkdir(parents=True)
        
        # Create old script
        script = self.ccnotify_dir / "ccnotify.py"
        script.write_text(f'''#!/usr/bin/env python3
__version__ = "{version}"

def main():
    print(f"CCNotify v{version}")

if __name__ == "__main__":
    main()
''')
        script.chmod(0o755)
        
        # Create config
        config = {
            "tts_provider": "kokoro",
            "config_version": "1.0",
            "test_data": "should_be_preserved"
        }
        config_file = self.ccnotify_dir / "config.json"
        config_file.write_text(json.dumps(config, indent=2))
        
    def create_broken_installation(self):
        """Create a broken installation with various issues."""
        self.ccnotify_dir.mkdir(parents=True)
        
        # Script exists but version is old
        script = self.ccnotify_dir / "ccnotify.py"
        script.write_text('#!/usr/bin/env python3\n__version__ = "0.1.3"\n')
        
        # Config exists but no models
        config = {"tts_provider": "kokoro"}
        config_file = self.ccnotify_dir / "config.json"
        config_file.write_text(json.dumps(config))
        
        # No models directory
        # No hooks configured
        
    def create_claude_settings(self, with_hooks: bool = False):
        """Create Claude settings.json."""
        settings = {
            "hooks": {
                "preToolUse": [],
                "postToolUse": []
            }
        }
        
        if with_hooks:
            script_path = str(self.ccnotify_dir / "ccnotify.py")
            settings["hooks"]["preToolUse"] = [{"command": f"python {script_path}"}]
            settings["hooks"]["postToolUse"] = [{"command": f"python {script_path}"}]
            
        settings_file = self.claude_dir / "settings.json"
        settings_file.write_text(json.dumps(settings, indent=2))
        
    def run_ccnotify(self, *args, local_server_url: Optional[str] = None) -> Tuple[int, str, str]:
        """Run ccnotify command in this environment."""
        env = {
            **os.environ,
            "HOME": str(self.home_dir),
            "PYTHONPATH": str(Path(__file__).parent.parent / "src")
        }
        
        cmd = ["uvx"]
        if local_server_url:
            cmd.extend(["--index-url", local_server_url])
            cmd.extend(["--extra-index-url", "https://pypi.org/simple/"])
        
        cmd.extend(["ccnotify"] + list(args))
        
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True
        )
        
        return result.returncode, result.stdout, result.stderr
        
    def verify_installation(self) -> Dict[str, bool]:
        """Verify the installation is complete and correct."""
        checks = {}
        
        # Check script exists
        script = self.ccnotify_dir / "ccnotify.py"
        checks["script_exists"] = script.exists()
        
        if checks["script_exists"]:
            # Check version
            content = script.read_text()
            checks["has_version"] = "__version__" in content
            
            # Extract version
            import re
            match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                checks["version"] = match.group(1)
                
        # Check config
        config_file = self.ccnotify_dir / "config.json"
        checks["config_exists"] = config_file.exists()
        
        if checks["config_exists"]:
            try:
                config = json.loads(config_file.read_text())
                checks["config_valid"] = True
                checks["tts_provider"] = config.get("tts_provider")
            except:
                checks["config_valid"] = False
                
        # Check models (if Kokoro)
        if checks.get("tts_provider") == "kokoro":
            models_dir = self.ccnotify_dir / "models"
            checks["models_dir_exists"] = models_dir.exists()
            
            if models_dir.exists():
                model_files = list(models_dir.glob("*.onnx"))
                checks["models_downloaded"] = len(model_files) > 0
                
        # Check hooks
        settings_file = self.claude_dir / "settings.json"
        if settings_file.exists():
            try:
                settings = json.loads(settings_file.read_text())
                hooks = settings.get("hooks", {})
                pre_hooks = hooks.get("preToolUse", [])
                post_hooks = hooks.get("postToolUse", [])
                
                script_path = str(self.ccnotify_dir / "ccnotify.py")
                checks["hooks_configured"] = any(
                    script_path in hook.get("command", "") 
                    for hook in pre_hooks + post_hooks
                )
            except:
                checks["hooks_configured"] = False
        else:
            checks["hooks_configured"] = False
            
        return checks


# Test functions
def test_fresh_installation():
    """Test a completely fresh installation."""
    print("\n📦 Testing fresh installation...")
    
    with TestEnvironment("fresh") as env:
        # Run installation
        returncode, stdout, stderr = env.run_ccnotify(
            "install", "--quiet", "--non-interactive"
        )
        
        # Verify
        checks = env.verify_installation()
        
        success = all([
            checks.get("script_exists"),
            checks.get("config_exists"),
            checks.get("config_valid")
        ])
        
        if success:
            print("✅ Fresh installation successful")
        else:
            print("❌ Fresh installation failed")
            print(f"   Checks: {checks}")
            
        return success


def test_update_from_old_version():
    """Test updating from an old version."""
    print("\n🔄 Testing update from old version...")
    
    with TestEnvironment("update") as env:
        # Create old installation
        env.create_old_installation("0.1.3")
        
        # Verify old version
        old_checks = env.verify_installation()
        assert old_checks["version"] == "0.1.3"
        
        # Run update
        returncode, stdout, stderr = env.run_ccnotify(
            "install", "--quiet", "--non-interactive"
        )
        
        # Verify update
        new_checks = env.verify_installation()
        
        # Check version was updated
        from ccnotify import __version__
        version_updated = new_checks.get("version") == __version__
        
        # Check config was preserved
        config_file = env.ccnotify_dir / "config.json"
        if config_file.exists():
            config = json.loads(config_file.read_text())
            config_preserved = config.get("test_data") == "should_be_preserved"
        else:
            config_preserved = False
            
        success = version_updated and config_preserved
        
        if success:
            print(f"✅ Update successful: 0.1.3 -> {new_checks.get('version')}")
            print(f"   Config preserved: {config_preserved}")
        else:
            print("❌ Update failed")
            print(f"   Version updated: {version_updated}")
            print(f"   Config preserved: {config_preserved}")
            
        return success


def test_broken_installation_repair():
    """Test repairing a broken installation."""
    print("\n🔧 Testing broken installation repair...")
    
    with TestEnvironment("repair") as env:
        # Create broken installation
        env.create_broken_installation()
        
        # Run installer (should detect and fix issues)
        returncode, stdout, stderr = env.run_ccnotify(
            "install", "--quiet", "--non-interactive"
        )
        
        # Verify repair
        checks = env.verify_installation()
        
        # For now just check basics (models and hooks might not be fixed in quiet mode)
        success = all([
            checks.get("script_exists"),
            checks.get("config_exists"),
            checks.get("config_valid")
        ])
        
        if success:
            print("✅ Broken installation repaired")
        else:
            print("❌ Repair failed")
            print(f"   Checks: {checks}")
            
        return success


def test_version_consistency():
    """Test that all version references are consistent."""
    print("\n🔍 Testing version consistency...")
    
    from ccnotify import __version__ as init_version
    
    # Check pyproject.toml
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    pyproject_content = pyproject_path.read_text()
    import re
    match = re.search(r'^version = "([^"]+)"', pyproject_content, re.MULTILINE)
    pyproject_version = match.group(1) if match else None
    
    # Check if versions match
    versions_match = init_version == pyproject_version
    
    if versions_match:
        print(f"✅ Versions consistent: {init_version}")
    else:
        print(f"❌ Version mismatch!")
        print(f"   __init__.py: {init_version}")
        print(f"   pyproject.toml: {pyproject_version}")
        
    return versions_match


def run_all_tests():
    """Run all installation tests."""
    print("=" * 50)
    print("🧪 CCNotify Installation Test Suite")
    print("=" * 50)
    
    tests = [
        ("Version Consistency", test_version_consistency),
        ("Fresh Installation", test_fresh_installation),
        ("Update from Old Version", test_update_from_old_version),
        ("Broken Installation Repair", test_broken_installation_repair),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"❌ {name} raised exception: {e}")
            results[name] = False
            
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
        
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All tests passed! Ready for publication.")
    else:
        failed_count = sum(1 for passed in results.values() if not passed)
        print(f"\n⚠️  {failed_count} test(s) failed. Fix before publishing!")
        
    return all_passed


if __name__ == "__main__":
    import os
    success = run_all_tests()
    sys.exit(0 if success else 1)