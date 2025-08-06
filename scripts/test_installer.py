#!/usr/bin/env python3
"""
Local testing script for CCNotify installer
Tests various installation scenarios without publishing to PyPI
"""

import sys
import tempfile
import shutil
from pathlib import Path
import subprocess
import os

# Add src to path for direct imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ccnotify.installer.flows import FirstTimeFlow, UpdateFlow
from ccnotify.installer.detector import InstallationDetector
from ccnotify.cli import execute_install_command


def run_test(test_name: str, test_func):
    """Run a single test with error handling."""
    print(f"\n{'='*60}")
    print(f"Running: {test_name}")
    print('='*60)
    
    try:
        result = test_func()
        if result:
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
        return result
    except Exception as e:
        print(f"❌ {test_name} FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fresh_install_with_kokoro():
    """Test fresh installation with Kokoro model download."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Override home directory
        os.environ['HOME'] = tmpdir
        
        # Simulate user input for Kokoro selection
        # Note: This requires mocking user input or using a quiet mode
        print("Testing fresh install with Kokoro...")
        
        flow = FirstTimeFlow()
        # Test the Kokoro setup directly
        kokoro_config = flow._setup_kokoro()
        
        return kokoro_config is not None and kokoro_config.get('models_downloaded') == True


def test_model_download_failure():
    """Test handling of model download failure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['HOME'] = tmpdir
        
        # Temporarily break the model download URL
        from ccnotify import setup
        original_models = setup.setup_kokoro.__code__.co_consts
        
        # Simulate network failure
        import requests
        original_get = requests.get
        
        def mock_get(*args, **kwargs):
            raise requests.exceptions.ConnectionError("Simulated network failure")
        
        requests.get = mock_get
        
        try:
            flow = FirstTimeFlow()
            kokoro_config = flow._setup_kokoro()
            
            # Should return None on failure
            return kokoro_config is None
        finally:
            requests.get = original_get


def test_update_flow():
    """Test update flow with existing installation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['HOME'] = tmpdir
        
        # Create a fake existing installation
        claude_dir = Path(tmpdir) / ".claude"
        ccnotify_dir = claude_dir / "ccnotify"
        ccnotify_dir.mkdir(parents=True)
        
        # Create dummy files
        (ccnotify_dir / "ccnotify.py").write_text("# dummy script")
        (ccnotify_dir / "config.json").write_text('{"tts_provider": "none"}')
        
        # Test update flow
        flow = UpdateFlow()
        detector = InstallationDetector()
        status = detector.check_existing_installation()
        
        return status.exists and status.script_version is not None


def test_cli_command():
    """Test the main CLI install command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['HOME'] = tmpdir
        
        # Test with quiet mode to avoid user interaction
        result = execute_install_command(quiet=True, force=True)
        
        # Check if files were created
        ccnotify_dir = Path(tmpdir) / ".claude" / "ccnotify"
        return ccnotify_dir.exists() and (ccnotify_dir / "ccnotify.py").exists()


def test_migration_from_legacy():
    """Test migration from legacy hooks directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['HOME'] = tmpdir
        
        # Create legacy installation
        claude_dir = Path(tmpdir) / ".claude"
        hooks_dir = claude_dir / "hooks"
        hooks_dir.mkdir(parents=True)
        
        # Create legacy files
        (hooks_dir / "notify.py").write_text("# legacy script")
        (hooks_dir / ".env").write_text("TTS_PROVIDER=kokoro")
        
        # Test migration detection
        detector = InstallationDetector()
        
        return detector.needs_migration()


def main():
    """Run all tests."""
    print("🧪 CCNotify Installer Test Suite")
    print("================================")
    
    tests = [
        ("Fresh Install with Kokoro", test_fresh_install_with_kokoro),
        ("Model Download Failure Handling", test_model_download_failure),
        ("Update Flow Detection", test_update_flow),
        ("CLI Install Command", test_cli_command),
        ("Legacy Migration Detection", test_migration_from_legacy),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        if run_test(test_name, test_func):
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Test Results: {passed} passed, {failed} failed")
    print('='*60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)