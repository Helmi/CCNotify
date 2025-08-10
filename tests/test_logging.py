"""Tests for optional logging functionality."""

import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest


def test_logging_flag_precedence():
    """Test that --logging flag overrides environment variable."""
    from src.ccnotify.notify import setup_logging, NoOpLogger
    
    # Create a temporary directory for logs
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('src.ccnotify.notify.LOGS_DIR', Path(temp_dir) / 'logs'):
            # Test that command-line flag takes precedence
            with patch('src.ccnotify.notify.USE_LOGGING', True):
                # Flag says False, env says True - should be disabled
                setup_logging(enable_logging=False)
                from src.ccnotify.notify import logger
                assert isinstance(logger, NoOpLogger), "Logging should be disabled when flag is False"
            
            # Test that flag enables logging even when env is False
            with patch('src.ccnotify.notify.USE_LOGGING', False):
                setup_logging(enable_logging=True)
                from src.ccnotify.notify import logger
                # Logger should be a real logger, not NoOpLogger
                assert hasattr(logger, 'handlers'), "Logging should be enabled when flag is True"


def test_hook_command_updates_with_logging():
    """Test that existing hooks get updated with/without --logging flag."""
    from src.ccnotify.cli import update_claude_settings
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a mock Claude directory
        claude_dir = Path(temp_dir) / '.claude'
        claude_dir.mkdir()
        settings_file = claude_dir / 'settings.json'
        
        # Create initial settings with existing hook
        import json
        initial_settings = {
            "hooks": {
                "PreToolUse": [{
                    "matcher": ".*",
                    "hooks": [{
                        "type": "command",
                        "command": "uv run /path/to/ccnotify.py"
                    }]
                }]
            },
            "hooksEnabled": True
        }
        
        with open(settings_file, 'w') as f:
            json.dump(initial_settings, f)
        
        with patch('src.ccnotify.cli.Path.home', return_value=Path(temp_dir)):
            # Update with logging enabled
            result = update_claude_settings("/path/to/ccnotify.py", logging=True)
            assert result == True
            
            # Check that command was updated
            with open(settings_file, 'r') as f:
                settings = json.load(f)
            
            command = settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
            assert "--logging" in command, "Command should include --logging flag"
            
            # Update with logging disabled
            result = update_claude_settings("/path/to/ccnotify.py", logging=False)
            assert result == True
            
            # Check that command was updated
            with open(settings_file, 'r') as f:
                settings = json.load(f)
            
            command = settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
            assert "--logging" not in command, "Command should not include --logging flag"


def test_no_log_directory_when_disabled():
    """Verify no log directory is created when logging is disabled."""
    from src.ccnotify.notify import setup_logging
    
    with tempfile.TemporaryDirectory() as temp_dir:
        logs_dir = Path(temp_dir) / 'logs'
        
        with patch('src.ccnotify.notify.LOGS_DIR', logs_dir):
            # Setup with logging disabled
            setup_logging(enable_logging=False)
            
            # Verify logs directory was not created
            assert not logs_dir.exists(), "Logs directory should not be created when logging is disabled"
            
            # Setup with logging enabled
            setup_logging(enable_logging=True)
            
            # Verify logs directory was created
            assert logs_dir.exists(), "Logs directory should be created when logging is enabled"


def test_log_rotation():
    """Test that log files are rotated when they exceed size limit."""
    from src.ccnotify.notify import setup_logging
    import datetime
    
    with tempfile.TemporaryDirectory() as temp_dir:
        logs_dir = Path(temp_dir) / 'logs'
        logs_dir.mkdir()
        
        # Create a large log file
        log_file = logs_dir / f"notifications_{datetime.datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, 'w') as f:
            # Write 11MB of data (exceeds 10MB limit)
            f.write('x' * (11 * 1024 * 1024))
        
        original_size = log_file.stat().st_size
        
        with patch('src.ccnotify.notify.LOGS_DIR', logs_dir):
            # Setup logging which should trigger rotation
            setup_logging(enable_logging=True)
            
            # Check that original file was rotated
            assert not log_file.exists() or log_file.stat().st_size < original_size
            
            # Check that a backup file was created
            backup_files = list(logs_dir.glob("notifications_*.*.log"))
            assert len(backup_files) > 0, "Backup file should be created during rotation"


def test_permission_error_handling():
    """Test that permission errors are handled gracefully."""
    from src.ccnotify.notify import setup_logging, NoOpLogger
    
    with tempfile.TemporaryDirectory() as temp_dir:
        logs_dir = Path(temp_dir) / 'logs'
        
        with patch('src.ccnotify.notify.LOGS_DIR', logs_dir):
            # Mock mkdir to raise PermissionError
            with patch.object(Path, 'mkdir', side_effect=PermissionError("No permission")):
                with patch('sys.stderr', new_callable=MagicMock):
                    setup_logging(enable_logging=True)
                    
                    from src.ccnotify.notify import logger
                    assert isinstance(logger, NoOpLogger), "Should fall back to NoOpLogger on permission error"


def test_parameter_validation():
    """Test that invalid parameters are rejected."""
    from src.ccnotify.cli import execute_install_command
    
    # Test with invalid logging parameter
    with pytest.raises(TypeError, match="logging parameter must be a boolean"):
        execute_install_command(logging="yes")  # Should be boolean, not string


if __name__ == "__main__":
    pytest.main([__file__, "-v"])