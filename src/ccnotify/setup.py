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
import json
import sys
from pathlib import Path
from typing import Dict, Tuple
from datetime import datetime
import requests
from tqdm import tqdm


def download_with_progress(url: str, output_path: Path, expected_size: int = None) -> bool:
    """Download a file with progress bar"""
    try:
        print(f"Downloading {output_path.name}...")

        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = expected_size or int(response.headers.get("content-length", 0))

        with open(output_path, "wb") as f:
            with tqdm(total=total_size, unit="B", unit_scale=True, desc=output_path.name) as pbar:
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


def get_latest_model_info() -> dict:
    """Get latest model release info from GitHub"""
    try:
        url = "https://api.github.com/repos/thewh1teagle/kokoro-onnx/releases/latest"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"⚠️  Could not check for updates: {e}")
        return None


def save_model_info(models_dir: Path, release_info: dict):
    """Save model version info"""
    info = {
        "version": release_info.get("tag_name", "unknown"),
        "updated_at": datetime.now().isoformat(),
        "release_date": release_info.get("published_at", "unknown"),
    }

    info_file = models_dir / "model_info.json"
    with open(info_file, "w") as f:
        json.dump(info, f, indent=2)


def get_current_model_info(models_dir: Path) -> dict:
    """Get current model version info"""
    info_file = models_dir / "model_info.json"
    if info_file.exists():
        try:
            with open(info_file, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def setup_kokoro(force_download: bool = False) -> bool:
    """Download and setup Kokoro TTS models"""
    print("🔧 Setting up Kokoro TTS...")

    # Create models directory
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)

    # Model files with expected sizes
    models = {
        "kokoro-v1.0.onnx": {
            "url": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
            "size": 325532387,  # ~310MB
        },
        "voices-v1.0.bin": {
            "url": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
            "size": 28214398,  # ~27MB
        },
    }

    # Check if models already exist
    models_exist = all((models_dir / filename).exists() for filename in models.keys())

    if models_exist and not force_download:
        print("✅ Kokoro models already installed (use --force to reinstall)")
        return True

    success = True

    for filename, info in models.items():
        file_path = models_dir / filename

        # Skip if file exists and not forcing download
        if file_path.exists() and not force_download:
            print(f"✓ {filename} already exists")
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
        # Save version info
        latest_release = get_latest_model_info()
        if latest_release:
            save_model_info(models_dir, latest_release)

        print("✅ Kokoro TTS setup completed successfully!")
        print("\nTo use Kokoro TTS:")
        print("1. Set TTS_PROVIDER=kokoro in your .env file")
        print("2. Configure KOKORO_VOICE (e.g., af_heart, am_adam)")
        print("3. Optionally set KOKORO_SPEED (0.5-2.0)")

        # Test installation
        print("\n🧪 Testing installation...")
        try:
            from .tts.kokoro import KokoroProvider

            # Create proper config for KokoroProvider
            test_config = {"models_dir": str(models_dir), "voice": "af_heart", "speed": 1.0}
            provider = KokoroProvider(test_config)
            if provider.is_available():
                print("✅ Kokoro TTS installation verified!")
            else:
                print("⚠️  Kokoro TTS installed but models not available")
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
        "English (Female)": [
            "af_alloy",
            "af_aoede",
            "af_bella",
            "af_heart",
            "af_jessica",
            "af_kore",
            "af_nicole",
            "af_nova",
            "af_river",
            "af_sarah",
            "af_sky",
        ],
        "English (Male)": [
            "am_adam",
            "am_echo",
            "am_eric",
            "am_fenrir",
            "am_liam",
            "am_michael",
            "am_onyx",
            "am_puck",
            "am_santa",
        ],
        "British English (Female)": ["bf_alice", "bf_emma", "bf_isabella", "bf_lily"],
        "British English (Male)": ["bm_daniel", "bm_fable", "bm_george", "bm_lewis"],
        "French": ["ff_siwis"],
        "Italian": ["if_sara", "im_nicola"],
        "Japanese": ["jf_alpha", "jf_gongitsune", "jf_nezumi", "jf_tebukuro", "jm_kumo"],
        "Chinese": [
            "zf_xiaobei",
            "zf_xiaoni",
            "zf_xiaoxiao",
            "zf_xiaoyi",
            "zm_yunjian",
            "zm_yunxi",
            "zm_yunxia",
            "zm_yunyang",
        ],
    }

    print("🎤 Available Kokoro TTS Voices:")
    print()

    for category, voice_list in voices.items():
        print(f"{category}:")
        for voice in voice_list:
            print(f"  • {voice}")
        print()

    print("💡 Voice Blending Examples:")
    print("  • af_heart:60,am_adam:40  (60% Heart + 40% Adam)")
    print("  • af_bella:80,af_nova:20  (80% Bella + 20% Nova)")


def check_and_update() -> bool:
    """
    Check for updates to both package and models, guide user through updates
    """
    print("🔍 Checking for updates...")

    # Check package version
    try:
        import subprocess

        result = subprocess.run(
            ["pip", "show", "ccnotify"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if line.startswith("Version:"):
                    current_pkg_version = line.split(":")[1].strip()
                    print(f"📦 Current package version: {current_pkg_version}")
                    break
        else:
            print("📦 Package not installed via pip (development mode?)")
    except Exception as e:
        print(f"⚠️  Could not check package version: {e}")

    # Check model version
    models_dir = Path("models")
    current_model_info = get_current_model_info(models_dir)
    latest_release = get_latest_model_info()

    updates_available = False

    if latest_release:
        latest_version = latest_release.get("tag_name", "unknown")
        current_version = current_model_info.get("version", "none")

        print(f"🎤 Current model version: {current_version}")
        print(f"🎤 Latest model version: {latest_version}")

        if current_version != latest_version:
            updates_available = True
            print(f"\n📦 Model update available: {current_version} → {latest_version}")
        else:
            print("✅ Models are up to date!")
    else:
        print("⚠️  Could not check for model updates")

    if updates_available:
        print("\n🚀 Updates available!")
        response = input("Update models now? [Y/n]: ").strip().lower()

        if response in ["", "y", "yes"]:
            return setup_kokoro(force_download=True)
        else:
            print("⏭️  Skipping model update")

    print("\n💡 To update the package, run: pip install --upgrade ccnotify")
    return True


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
    if response.lower() == "y":
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
  python setup.py --kokoro --force  Reinstall Kokoro models
  python setup.py --update          Check for and install updates
  python setup.py --voices          List available voices
  python setup.py --cleanup         Remove downloaded models
        """,
    )

    parser.add_argument("--kokoro", action="store_true", help="Setup Kokoro TTS")
    parser.add_argument("--force", action="store_true", help="Force reinstall models")
    parser.add_argument("--update", action="store_true", help="Check for and install updates")
    parser.add_argument("--voices", action="store_true", help="List available voices")
    parser.add_argument("--cleanup", action="store_true", help="Clean up downloaded models")

    args = parser.parse_args()

    if not any([args.kokoro, args.update, args.voices, args.cleanup]):
        parser.print_help()
        return

    if args.voices:
        list_voices()

    if args.update:
        success = check_and_update()
        if not success:
            sys.exit(1)

    elif args.kokoro:
        success = setup_kokoro(force_download=args.force)
        if not success:
            sys.exit(1)

    elif args.cleanup:
        cleanup_models()


if __name__ == "__main__":
    main()
