#!/bin/bash
# Complete installer test in isolated environment

set -e

echo "🧪 CCNotify Complete Installer Test"
echo "==================================="

# Create temporary directory
TEMP_DIR=$(mktemp -d)
echo "📁 Test directory: $TEMP_DIR"

# Create virtual environment
echo "🐍 Creating virtual environment..."
python3 -m venv "$TEMP_DIR/venv"
source "$TEMP_DIR/venv/bin/activate"

# Install dependencies
echo "📦 Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet requests tqdm rich pytest

# Set up test home
export TEST_HOME="$TEMP_DIR/home"
mkdir -p "$TEST_HOME/.claude"

# Create fake settings.json
cat > "$TEST_HOME/.claude/settings.json" << 'EOF'
{
    "version": "1.0",
    "hooks": {
        "preToolUse": [],
        "postToolUse": []
    }
}
EOF

# Set HOME to test directory
export HOME="$TEST_HOME"
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

echo "📍 Test HOME: $HOME"
echo "📍 Python: $(which python)"
echo "📍 PYTHONPATH: $PYTHONPATH"

# Test 1: KokoroProvider fix
echo -e "\n🧪 Test 1: KokoroProvider initialization"
echo "----------------------------------------"

python3 << 'EOF'
import sys
import tempfile
from pathlib import Path

# Test the fix
try:
    from ccnotify.tts.kokoro import KokoroProvider
    
    with tempfile.TemporaryDirectory() as tmpdir:
        models_dir = Path(tmpdir) / "models"
        models_dir.mkdir()
        
        # Create dummy files
        (models_dir / "kokoro-v1.0.onnx").write_text("dummy")
        (models_dir / "voices-v1.0.bin").write_text("dummy")
        
        # Test with config dict (should work)
        config = {
            "models_dir": str(models_dir),
            "voice": "af_sarah",
            "speed": 1.0
        }
        
        provider = KokoroProvider(config)
        print("✅ KokoroProvider created successfully with config dict")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
EOF

# Test 2: Setup script
echo -e "\n🧪 Test 2: setup.py --kokoro"
echo "----------------------------"

cd "$HOME/.claude"
mkdir -p ccnotify
cd ccnotify

# Run setup with force to test the fix
python "$(pwd)/src/ccnotify/setup.py" --kokoro --force 2>&1 | grep -E "(Testing installation|Installation test|Error|Failed|Success)" || true

# Test 3: Full installer flow
echo -e "\n🧪 Test 3: Full installer flow"
echo "-------------------------------"

python3 << 'EOF'
import os
os.environ['HOME'] = os.environ['TEST_HOME']

from ccnotify.cli import execute_install_command

# Test quiet installation
success = execute_install_command(quiet=True, force=True)
print(f"Installation success: {success}")

# Check what was created
ccnotify_dir = os.path.join(os.environ['HOME'], '.claude', 'ccnotify')
if os.path.exists(ccnotify_dir):
    print(f"✅ Created: {ccnotify_dir}")
    for item in os.listdir(ccnotify_dir):
        print(f"   - {item}")
else:
    print("❌ CCNotify directory not created")
EOF

# Cleanup
deactivate
rm -rf "$TEMP_DIR"

echo -e "\n✅ All tests completed"