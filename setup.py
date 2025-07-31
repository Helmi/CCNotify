#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "requests",
#     "tqdm",
# ]
# ///

"""
CCNotify Setup Script
Handles installation and configuration of TTS providers
"""

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Dict, Tuple
import requests
from tqdm import tqdm


def download_with_progress(url: str, output_path: Path, expected_size: int = None) -> bool:
    """Download a file with progress bar"""
    try:
        print(f"Downloading {output_path.name}...")
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = expected_size or int(response.headers.get('content-length', 0))
        
        with open(output_path, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=output_path.name) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        
        print(f"✓ Downloaded {output_path.name}")
        return True
    
    except Exception as e:
        print(f"✗ Failed to download {output_path.name}: {e}")
        if output_path.exists():
            output_path.unlink()
        return False


def verify_file_hash(file_path: Path, expected_hash: str) -> bool:
    """Verify file integrity using SHA256 hash"""
    if not file_path.exists():
        return False
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest() == expected_hash


def setup_kokoro(update: bool = False) -> bool:
    """Download and setup Kokoro TTS models"""
    print("🔧 Setting up Kokoro TTS...")
    
    # Create models directory
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # Model files with expected sizes and hashes
    models = {
        "kokoro-v1.0.onnx": {
            "url": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
            "size": 325532387,  # ~310MB
            "hash": "e7c4b4d1c2a8e7f5d5c8e1f4c2a7b9e3d4f6a8c9e1b7f2d5c8a3e9f1b6d4c7a2"  # Placeholder
        },
        "voices-v1.0.bin": {
            "url": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
            "size": 28214398,   # ~27MB
            "hash": "f8a2e1d3c7b9e4f6a5c8d2e9f1b3a7c4e6d8b2f5a9c1e4f7b3d6a8c2e5f9b1d4"  # Placeholder
        }
    }
    
    success = True
    
    for filename, info in models.items():
        file_path = models_dir / filename
        
        # Skip if file exists and not updating
        if file_path.exists() and not update:
            print(f"✓ {filename} already exists (use --update to refresh)")
            continue
        
        # Download the file
        if not download_with_progress(info["url"], file_path, info["size"]):
            success = False
            continue
        
        # Verify file size
        actual_size = file_path.stat().st_size
        if actual_size != info["size"]:
            print(f"✗ {filename} size mismatch: expected {info['size']}, got {actual_size}")
            success = False
    
    if success:
        print("✅ Kokoro TTS setup completed successfully!")
        print("\nTo use Kokoro TTS:")
        print("1. Set TTS_PROVIDER=kokoro in your .env file")
        print("2. Configure KOKORO_VOICE (e.g., af_sarah, am_adam)")
        print("3. Optionally set KOKORO_SPEED (0.5-2.0)")
        
        # Test installation
        print("\n🧪 Testing installation...")
        try:
            from ccnotify.tts.kokoro import KokoroProvider
            provider = KokoroProvider(models_dir)
            print("✅ Kokoro TTS installation verified!")
        except ImportError:
            print("⚠️  Kokoro TTS installed, but ccnotify.tts module not found")
            print("   Run this after implementing the TTS provider system")
        except Exception as e:
            print(f"⚠️  Installation test failed: {e}")
    else:
        print("❌ Kokoro TTS setup failed")
    
    return success


def list_voices() -> None:
    """List available Kokoro voices"""
    voices = {
        "English (Female)": ["af_alloy", "af_aoede", "af_bella", "af_heart", "af_jessica", 
                            "af_kore", "af_nicole", "af_nova", "af_river", "af_sarah", "af_sky"],
        "English (Male)": ["am_adam", "am_echo", "am_eric", "am_fenrir", "am_liam", 
                          "am_michael", "am_onyx", "am_puck", "am_santa"],
        "British English (Female)": ["bf_alice", "bf_emma", "bf_isabella", "bf_lily"],
        "British English (Male)": ["bm_daniel", "bm_fable", "bm_george", "bm_lewis"],
        "French": ["ff_siwis"],
        "Italian": ["if_sara", "im_nicola"],
        "Japanese": ["jf_alpha", "jf_gongitsune", "jf_nezumi", "jf_tebukuro", "jm_kumo"],
        "Chinese": ["zf_xiaobei", "zf_xiaoni", "zf_xiaoxiao", "zf_xiaoyi", 
                   "zm_yunjian", "zm_yunxi", "zm_yunxia", "zm_yunyang"]
    }
    
    print("🎤 Available Kokoro TTS Voices:")
    print()
    
    for category, voice_list in voices.items():
        print(f"{category}:")
        for voice in voice_list:
            print(f"  • {voice}")
        print()
    
    print("💡 Voice Blending Examples:")
    print("  • af_sarah:60,am_adam:40  (60% Sarah + 40% Adam)")
    print("  • af_bella:80,af_nova:20  (80% Bella + 20% Nova)")


def cleanup_models() -> None:
    """Clean up downloaded model files"""
    models_dir = Path("models")
    
    if not models_dir.exists():
        print("No models directory found")
        return
    
    model_files = list(models_dir.glob("*.onnx")) + list(models_dir.glob("*.bin"))
    
    if not model_files:
        print("No model files found to clean up")
        return
    
    total_size = sum(f.stat().st_size for f in model_files)
    print(f"Found {len(model_files)} model files ({total_size / 1024 / 1024:.1f} MB)")
    
    response = input("Delete all model files? [y/N]: ")
    if response.lower() == 'y':
        for file_path in model_files:
            file_path.unlink()
            print(f"Deleted {file_path.name}")
        
        # Remove directory if empty
        if not any(models_dir.iterdir()):
            models_dir.rmdir()
            print("Removed empty models directory")
        
        print("✅ Cleanup completed")
    else:
        print("Cleanup cancelled")


def main():
    """Main setup script entry point"""
    parser = argparse.ArgumentParser(
        description="CCNotify Setup - Install and configure TTS providers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup.py --kokoro          Install Kokoro TTS
  python setup.py --kokoro --update Update Kokoro models
  python setup.py --voices          List available voices
  python setup.py --cleanup         Remove downloaded models
        """)
    
    parser.add_argument("--kokoro", action="store_true", help="Setup Kokoro TTS")
    parser.add_argument("--update", action="store_true", help="Update/redownload models")
    parser.add_argument("--voices", action="store_true", help="List available voices")
    parser.add_argument("--cleanup", action="store_true", help="Clean up downloaded models")
    
    args = parser.parse_args()
    
    if not any([args.kokoro, args.voices, args.cleanup]):
        parser.print_help()
        return
    
    if args.voices:
        list_voices()
    
    if args.kokoro:
        success = setup_kokoro(update=args.update)
        if not success:
            sys.exit(1)
    
    if args.cleanup:
        cleanup_models()


if __name__ == "__main__":
    main()