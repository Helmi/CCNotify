#!/usr/bin/env python3
"""
Test CCNotify installer in an isolated environment
"""

import os
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path
import json

def create_test_environment():
    """Create isolated test environment"""
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"🧪 Created test environment: {tmpdir}")
        
        # Create fake home directory structure
        test_home = Path(tmpdir) / "home"
        test_home.mkdir()
        
        # Create Claude directory
        claude_dir = test_home / ".claude"
        claude_dir.mkdir()
        
        # Create fake settings.json
        settings_file = claude_dir / "settings.json"
        settings_file.write_text(json.dumps({
            "version": "1.0",
            "hooks": {
                "preToolUse": [],
                "postToolUse": []
            }
        }, indent=2))
        
        # Set environment to use test home
        env = os.environ.copy()
        env['HOME'] = str(test_home)
        env['PYTHONPATH'] = str(Path(__file__).parent.parent / "src")
        
        print(f"📁 Test home directory: {test_home}")
        print(f"📁 Claude directory: {claude_dir}")
        
        return test_home, env

def test_setup_script():
    """Test the setup.py script directly"""
    test_home, env = create_test_environment()
    
    print("\n" + "="*60)
    print("Testing setup.py --kokoro")
    print("="*60)
    
    # Install dependencies first
    print("📦 Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "tqdm"], capture_output=True)
    
    # Run setup.py with Kokoro option
    setup_script = Path(__file__).parent.parent / "src" / "ccnotify" / "setup.py"
    
    # Change to ccnotify directory for models
    ccnotify_dir = test_home / ".claude" / "ccnotify"
    ccnotify_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        result = subprocess.run(
            [sys.executable, str(setup_script), "--kokoro", "--force"],
            env=env,
            capture_output=True,
            text=True,
            cwd=str(ccnotify_dir)
        )
        
        print("STDOUT:")
        print(result.stdout)
        print("\nSTDERR:")
        print(result.stderr)
        print(f"\nReturn code: {result.returncode}")
        
        # Check if models directory was created
        models_dir = ccnotify_dir / "models"
        if models_dir.exists():
            print(f"✅ Models directory created: {models_dir}")
            for file in models_dir.iterdir():
                print(f"   - {file.name} ({file.stat().st_size / 1024 / 1024:.1f} MB)")
        else:
            print("❌ Models directory not created")
            
    except Exception as e:
        print(f"❌ Error running setup.py: {e}")
        import traceback
        traceback.print_exc()

def test_installer_flow():
    """Test the full installer flow"""
    test_home, env = create_test_environment()
    
    print("\n" + "="*60)
    print("Testing installer flow")
    print("="*60)
    
    # Create a test script that runs the installer
    test_script = f"""
import sys
sys.path.insert(0, '{Path(__file__).parent.parent / "src"}')

from ccnotify.installer.flows import FirstTimeFlow
from ccnotify.installer.detector import InstallationDetector

# Test detection
detector = InstallationDetector()
status = detector.check_existing_installation()
print(f"Installation exists: {{status.exists}}")

# Test first-time flow (quiet mode)
flow = FirstTimeFlow()
# Mock the TTS provider selection
flow._setup_tts_provider = lambda quiet: {{"tts_provider": "kokoro", "models_downloaded": True}}

# Test install
success = flow.run(quiet=True)
print(f"Installation success: {{success}}")

# Check what was created
import os
home = os.environ['HOME']
ccnotify_dir = os.path.join(home, '.claude', 'ccnotify')
if os.path.exists(ccnotify_dir):
    print(f"✅ Created: {{ccnotify_dir}}")
    for item in os.listdir(ccnotify_dir):
        print(f"   - {{item}}")
"""
    
    try:
        result = subprocess.run(
            [sys.executable, "-c", test_script],
            env=env,
            capture_output=True,
            text=True
        )
        
        print("STDOUT:")
        print(result.stdout)
        print("\nSTDERR:")
        print(result.stderr)
        print(f"\nReturn code: {result.returncode}")
        
    except Exception as e:
        print(f"❌ Error testing installer: {e}")
        import traceback
        traceback.print_exc()

def test_kokoro_provider():
    """Test KokoroProvider initialization"""
    test_home, env = create_test_environment()
    
    print("\n" + "="*60)
    print("Testing KokoroProvider")
    print("="*60)
    
    # Create models directory in ccnotify dir
    ccnotify_dir = test_home / ".claude" / "ccnotify"
    ccnotify_dir.mkdir(exist_ok=True)
    models_dir = ccnotify_dir / "models"
    models_dir.mkdir(exist_ok=True)
    
    # Create dummy model files
    (models_dir / "kokoro-v1.0.onnx").write_text("dummy")
    (models_dir / "voices-v1.0.bin").write_text("dummy")
    
    test_script = f"""
import sys
sys.path.insert(0, '{Path(__file__).parent.parent / "src"}')

from ccnotify.tts.kokoro import KokoroProvider

# Test with proper config
config = {{
    "models_dir": "{models_dir}",
    "voice": "af_sarah",
    "speed": 1.0
}}

try:
    provider = KokoroProvider(config)
    print(f"✅ KokoroProvider created successfully")
    print(f"   Model path: {{provider.model_path}}")
    print(f"   Voices path: {{provider.voices_path}}")
    
    # Test availability check (will fail without real models)
    available = provider.is_available()
    print(f"   Available: {{available}}")
except Exception as e:
    print(f"❌ Error creating KokoroProvider: {{e}}")
    import traceback
    traceback.print_exc()
"""
    
    try:
        result = subprocess.run(
            [sys.executable, "-c", test_script],
            env=env,
            capture_output=True,
            text=True
        )
        
        print("STDOUT:")
        print(result.stdout)
        print("\nSTDERR:")
        print(result.stderr)
        print(f"\nReturn code: {result.returncode}")
        
    except Exception as e:
        print(f"❌ Error testing KokoroProvider: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all tests"""
    print("🧪 CCNotify Isolated Installer Tests")
    print("====================================\n")
    
    # Test individual components
    test_kokoro_provider()
    test_setup_script()
    test_installer_flow()
    
    print("\n✅ All tests completed")

if __name__ == "__main__":
    main()