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
from unittest.mock import patch, MagicMock

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
        
        # Create the ccnotify directory first
        ccnotify_dir = Path(tmpdir) / ".claude" / "ccnotify"
        ccnotify_dir.mkdir(parents=True, exist_ok=True)
        
        # Simulate user input for Kokoro selection
        # Note: This requires mocking user input or using a quiet mode
        print("Testing fresh install with Kokoro...")
        
        # Mock the setup_kokoro function to avoid actual downloads in CI
        with patch('ccnotify.installer.flows.setup_kokoro') as mock_setup:
            # Simulate successful setup without downloading
            mock_setup.return_value = True
            
            # Also mock the console to avoid interactive prompts
            with patch('ccnotify.installer.flows.console'):
                flow = FirstTimeFlow()
                # Test the Kokoro setup directly
                kokoro_config = flow._setup_kokoro()
                
                # Verify mock was called
                mock_setup.assert_called_once_with(force_download=False)
                
                return kokoro_config is not None and kokoro_config.get('models_downloaded') == True


def test_model_download_failure():
    """Test handling of model download failure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['HOME'] = tmpdir
        
        # Create the ccnotify directory first
        ccnotify_dir = Path(tmpdir) / ".claude" / "ccnotify"
        ccnotify_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock the setup_kokoro function to simulate failure
        with patch('ccnotify.installer.flows.setup_kokoro') as mock_setup:
            # Simulate failed setup
            mock_setup.return_value = False
            
            # Also mock the console to avoid interactive prompts
            with patch('ccnotify.installer.flows.console'):
                flow = FirstTimeFlow()
                kokoro_config = flow._setup_kokoro()
                
                # Should return None on failure
                return kokoro_config is None


def test_update_flow():
    """Test update flow with existing installation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['HOME'] = tmpdir
        
        # Create a fake existing installation
        claude_dir = Path(tmpdir) / ".claude"
        ccnotify_dir = claude_dir / "ccnotify"
        ccnotify_dir.mkdir(parents=True)
        
        # Create dummy files with version info
        script_content = '''#!/usr/bin/env python3
# CCNotify installation
__version__ = "0.1.0"
# dummy script
'''
        (ccnotify_dir / "ccnotify.py").write_text(script_content)
        (ccnotify_dir / "config.json").write_text('{"tts_provider": "none"}')
        
        # Test update flow
        flow = UpdateFlow()
        detector = InstallationDetector()
        status = detector.check_existing_installation()
        
        return status.exists


def test_cli_command():
    """Test the main CLI install command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['HOME'] = tmpdir
        
        # Create the necessary directories
        claude_dir = Path(tmpdir) / ".claude"
        ccnotify_dir = claude_dir / "ccnotify"
        ccnotify_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock all external dependencies
        with patch('ccnotify.installer.flows.setup_kokoro') as mock_setup_flows:
            mock_setup_flows.return_value = True
            with patch('ccnotify.setup.setup_kokoro') as mock_setup:
                mock_setup.return_value = True
                
                # Mock update_claude_settings where it's actually defined
                with patch('ccnotify.cli.update_claude_settings') as mock_update_settings:
                    mock_update_settings.return_value = True
                    
                    # Test with quiet mode to avoid user interaction
                    result = execute_install_command(quiet=True, force=True, logging=False)
                    
                    # Check if result is True (successful)
                    return result == True


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
    
    # Detect if running in CI environment
    is_ci = os.environ.get('CI') == 'true' or os.environ.get('GITHUB_ACTIONS') == 'true'
    if is_ci:
        print("📦 Running in CI environment - model downloads will be mocked")
    
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