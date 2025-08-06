#!/usr/bin/env python3
"""
Test Kokoro model download and installation test
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_kokoro_setup():
    """Test the full Kokoro setup including model download"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"🧪 Testing Kokoro setup in: {tmpdir}")
        
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        
        try:
            # Import setup function
            from ccnotify.setup import setup_kokoro
            
            print("\n1. Testing model download (this will download ~340MB)...")
            print("   Press Ctrl+C to skip download test\n")
            
            # Test setup with force download
            success = setup_kokoro(force_download=True)
            
            if success:
                print("\n✅ Kokoro setup completed successfully!")
                
                # Check created files
                models_dir = Path("models")
                if models_dir.exists():
                    print(f"\n📁 Models directory contents:")
                    for file in models_dir.iterdir():
                        size_mb = file.stat().st_size / 1024 / 1024
                        print(f"   - {file.name}: {size_mb:.1f} MB")
                
                # Test the installation verification
                print("\n2. Testing installation verification...")
                
                # This is the code from setup.py that was failing
                try:
                    from ccnotify.tts.kokoro import KokoroProvider
                    
                    test_config = {
                        "models_dir": str(models_dir),
                        "voice": "af_sarah",
                        "speed": 1.0
                    }
                    
                    provider = KokoroProvider(test_config)
                    if provider.is_available():
                        print("   ✅ Kokoro TTS installation verified!")
                        
                        # Try to actually use it
                        print("\n3. Testing actual TTS generation...")
                        test_text = "Hello, this is a test."
                        output_path = Path(tmpdir) / "test.wav"
                        
                        if provider.generate(test_text, output_path):
                            print(f"   ✅ Generated audio: {output_path} ({output_path.stat().st_size} bytes)")
                        else:
                            print("   ❌ Failed to generate audio")
                    else:
                        print("   ⚠️  Kokoro TTS installed but models not available")
                        
                except Exception as e:
                    print(f"   ❌ Installation test failed: {e}")
                    import traceback
                    traceback.print_exc()
                    
            else:
                print("\n❌ Kokoro setup failed")
                
        except KeyboardInterrupt:
            print("\n⏭️  Skipping download test")
            
            # Test with existing dummy files
            print("\n4. Testing with dummy model files...")
            models_dir = Path("models")
            models_dir.mkdir(exist_ok=True)
            
            # Create dummy files
            (models_dir / "kokoro-v1.0.onnx").write_text("dummy")
            (models_dir / "voices-v1.0.bin").write_text("dummy")
            
            # Test the provider initialization
            from ccnotify.tts.kokoro import KokoroProvider
            
            test_config = {
                "models_dir": str(models_dir),
                "voice": "af_sarah",
                "speed": 1.0
            }
            
            try:
                provider = KokoroProvider(test_config)
                print("   ✅ KokoroProvider initialized with dummy files")
                
                # This should return False with dummy files
                available = provider.is_available()
                print(f"   - Is available: {available} (expected: False with dummy files)")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                
        finally:
            os.chdir(original_cwd)

if __name__ == "__main__":
    test_kokoro_setup()