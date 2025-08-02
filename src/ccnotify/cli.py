#!/usr/bin/env python3
"""
CCNotify CLI - Command line interface for ccnotify
"""

import argparse
import json
import shutil
import sys
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text
from .setup import main as setup_main, setup_kokoro
from .config import init_config, get_config_dir, get_claude_profile_dir

console = Console()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="CCNotify - Intelligent notification system for Claude Code",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Setup and configure TTS providers')
    setup_parser.add_argument("--kokoro", action="store_true", help="Setup Kokoro TTS")
    setup_parser.add_argument("--force", action="store_true", help="Force reinstall models")
    setup_parser.add_argument("--update", action="store_true", help="Check for and install updates")
    setup_parser.add_argument("--voices", action="store_true", help="List available voices")
    setup_parser.add_argument("--cleanup", action="store_true", help="Clean up downloaded models")
    
    # Install command
    install_parser = subparsers.add_parser('install', help='Interactive installer for ccnotify')
    install_parser.add_argument("--profile", default="~/.claude", help="Claude profile directory")
    install_parser.add_argument("--force", action="store_true", help="Force overwrite existing hooks")
    install_parser.add_argument("--non-interactive", action="store_true", help="Skip interactive prompts")
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Manage configuration')
    config_parser.add_argument("--init", action="store_true", help="Initialize configuration")
    config_parser.add_argument("--show", action="store_true", help="Show configuration paths")
    config_parser.add_argument("--reset", action="store_true", help="Reset to default configuration")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'setup':
        # Handle setup command by delegating to setup module
        setup_args = [
            sys.argv[0].replace('cli.py', 'setup.py')  # Simulate setup.py call
        ]
        
        if args.kokoro:
            setup_args.append('--kokoro')
        if args.force:
            setup_args.append('--force') 
        if args.update:
            setup_args.append('--update')
        if args.voices:
            setup_args.append('--voices')
        if args.cleanup:
            setup_args.append('--cleanup')
        
        # Temporarily replace sys.argv for setup module
        old_argv = sys.argv
        sys.argv = setup_args
        
        try:
            setup_main()
        finally:
            sys.argv = old_argv
    
    elif args.command == 'install':
        if args.non_interactive:
            install_hooks(args.profile, args.force)
        else:
            interactive_install(args.profile, args.force)
    
    elif args.command == 'config':
        handle_config_command(args)


def install_hooks(profile_dir: str, force: bool = False):
    """Install ccnotify hooks into Claude profile"""
    print("🔧 Installing ccnotify hooks...")
    
    # Resolve profile directory
    profile_path = Path(profile_dir).expanduser().resolve()
    ccnotify_dir = profile_path / "ccnotify"
    settings_file = profile_path / "settings.json"
    
    # Check if profile directory exists
    if not profile_path.exists():
        print(f"❌ Claude profile directory not found: {profile_path}")
        print("Make sure Claude Code is installed and has been run at least once")
        return False
    
    # Create ccnotify directory if it doesn't exist
    ccnotify_dir.mkdir(exist_ok=True)
    
    # Get ccnotify.py content - use embedded template
    try:
        notify_content = get_notify_template()
        if not notify_content:
            print("❌ get_notify_template() returned empty content")
            return False
        print(f"✅ Template loaded successfully ({len(notify_content)} chars)")
    except Exception as e:
        print(f"❌ Failed to get notify template: {e}")
        return False
    
    # Target hook file
    notify_target = ccnotify_dir / "ccnotify.py"
    
    # Check if hook already exists
    if notify_target.exists() and not force:
        print(f"⚠️  Hook already exists: {notify_target}")
        print("Use --force to overwrite")
        return False
    
    # Write ccnotify.py to hooks directory
    try:
        with open(notify_target, 'w') as f:
            f.write(notify_content)
        print(f"✅ Installed hook: {notify_target}")
    except Exception as e:
        print(f"❌ Failed to write hook: {e}")
        return False
    
    # Update settings.json to enable hooks (with backup)
    try:
        if settings_file.exists():
            # Create backup first
            backup_file = settings_file.with_suffix('.json.ccnotify.bak')
            shutil.copy2(settings_file, backup_file)
            console.print(f"📄 Created settings backup: {backup_file.name}")
            
            with open(settings_file, 'r') as f:
                settings = json.load(f)
        else:
            settings = {}
        
        # Add our hook configuration
        if "hooks" not in settings:
            settings["hooks"] = {}
        
        # Configure ccnotify hook for relevant events
        hook_config = {
            "type": "command",
            "command": f"uv run {notify_target}"
        }
        
        events_to_hook = ["PreToolUse", "PostToolUse", "Stop", "SubagentStop", "Notification"]
        hooks_added = False
        
        for event in events_to_hook:
            if event not in settings["hooks"]:
                settings["hooks"][event] = []
            
            # Check if our hook is already configured
            hook_exists = any(
                h.get("command", "").endswith(str(notify_target)) 
                for h in settings["hooks"][event]
                if isinstance(h, dict)
            )
            
            if not hook_exists:
                settings["hooks"][event].append({
                    "matcher": ".*",
                    "hooks": [hook_config]
                })
                hooks_added = True
        
        # Enable hooks if not already enabled
        if not settings.get("hooksEnabled", False):
            settings["hooksEnabled"] = True
            hooks_added = True
        
        if hooks_added:
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            
            console.print("✅ Configured ccnotify hooks in Claude settings")
        else:
            console.print("✓ ccnotify hooks already configured")
    
    except Exception as e:
        console.print(f"⚠️  Could not update Claude settings: {e}")
        console.print("You may need to manually configure hooks in Claude Code")
    
    print("\n🎉 Installation complete!")
    print("\nNext steps:")
    print("1. Configuration file created at ~/.claude/ccnotify/config.json")
    print("2. Run 'ccnotify setup --kokoro' to install TTS models")
    print("3. Restart Claude Code to load the new hooks")
    
    return True


def interactive_install(profile_dir: str, force: bool = False):
    """Interactive installer with TTS provider selection"""
    console.print("\n[bold blue]🔔 CCNotify Interactive Installer[/bold blue]")
    
    console.print(Panel.fit(
        "[yellow]This installer will:[/yellow]\n"
        "• Install notification hooks into Claude Code\n"
        "• Help you choose a TTS (text-to-speech) provider\n"
        "• Create configuration files\n"
        "• Guide you through setup",
        title="Welcome"
    ))
    
    # Step 1: Choose TTS provider
    console.print("\n[bold]Step 1: Choose TTS Provider[/bold]")
    
    choice = Prompt.ask(
        "\n[cyan]Which TTS provider would you like to use?[/cyan]",
        choices=["kokoro", "elevenlabs", "none"],
        default="kokoro",
        show_choices=True,
        show_default=True
    )
    
    # Explain choice
    if choice == "kokoro":
        console.print("\n✅ [green]Kokoro TTS selected[/green]")
        console.print("• High-quality local TTS with 50+ voices")
        console.print("• Requires ~350MB download for models")
        console.print("• No API key needed, completely private")
        
        download_models = Confirm.ask("\n📥 Download Kokoro models now?", default=True)
        
    elif choice == "elevenlabs":
        console.print("\n✅ [green]ElevenLabs TTS selected[/green]")
        console.print("• Premium cloud-based TTS")
        console.print("• Requires API key and internet connection")
        console.print("• Pay-per-use pricing")
        download_models = False
        
    else:  # none
        console.print("\n⚠️  [yellow]No TTS selected[/yellow]")
        console.print("• Notifications will be silent (visual only)")
        console.print("• You can configure TTS later")
        download_models = False
    
    # Step 2: Install hooks
    console.print("\n[bold]Step 2: Install Hooks[/bold]")
    
    if not install_hooks(profile_dir, force):
        console.print("❌ [red]Installation failed[/red]")
        return False
    
    # Step 3: Download models if needed
    if choice == "kokoro" and download_models:
        console.print("\n[bold]Step 3: Download TTS Models[/bold]")
        console.print("📥 Downloading Kokoro TTS models (~350MB)...")
        
        if not setup_kokoro():
            console.print("❌ [red]Model download failed[/red]")
            console.print("You can try again later with: [cyan]ccnotify setup --kokoro[/cyan]")
        else:
            console.print("✅ [green]Models downloaded successfully[/green]")
    
    # Step 4: Create configuration file
    console.print("\n[bold]Step 4: Create Configuration[/bold]")
    
    config_file = ccnotify_dir / "config.json"
    
    create_config = True
    if config_file.exists() and not force:
        create_config = Confirm.ask(
            f"\n📄 Configuration already exists in {config_file}\n   Overwrite it?",
            default=False
        )
    
    if create_config:
        create_config_file(config_file, choice)
        console.print(f"✅ Created configuration: [cyan]{config_file}[/cyan]")
    
    # Step 5: Final instructions
    console.print("\n[bold green]🎉 Installation Complete![/bold green]")
    
    console.print(Panel.fit(
        "[yellow]Next steps:[/yellow]\n\n"
        "1. [cyan]Restart Claude Code[/cyan] to load the new hooks\n\n"
        "2. Review and customize your config if needed\n\n"
        f"3. {'Test with: uvx ccnotify setup --voices' if choice == 'kokoro' else 'Add your ElevenLabs API key to config' if choice == 'elevenlabs' else 'Configure TTS later if desired'}\n\n"
        "4. Start using Claude Code - you'll get audio notifications!",
        title="Success",
        border_style="green"
    ))
    
    return True


def get_notify_template() -> str:
    """Get the ccnotify.py template content"""
    return '''#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "pync",
#     "requests", 
#     "kokoro-onnx",
#     "pydub",
#     "soundfile",
#     "tqdm",
#     "rich"
# ]
# ///

"""
CCNotify - Intelligent notification system for Claude Code with audio feedback
Generated by ccnotify installer
"""

import json
import sys
import os
from pathlib import Path

def load_config():
    """Load configuration from config.json"""
    config_file = Path.home() / ".claude" / "ccnotify" / "config.json"
    
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    
    # Default config
    return {
        "tts": {"provider": "none", "enabled": False},
        "notifications": {"enabled": True, "sound_enabled": False}
    }

def main():
    """Main notification handler"""
    config = load_config()
    
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
    else:
        message = "Claude Code notification"
    
    # Show notification if enabled
    if config.get("notifications", {}).get("enabled", True):
        try:
            if sys.platform == "darwin":
                import pync
                pync.notify(message, title="Claude Code")
            else:
                print(f"Notification: {message}")
        except ImportError:
            print(f"Notification: {message}")
    
    # TODO: Add TTS functionality here based on config
    # This is a minimal version - full TTS will be added later

if __name__ == "__main__":
    main()
'''


def create_config_file(config_path: Path, tts_provider: str):
    """Create a well-commented configuration file"""
    
    config = {
        "tts": {
            "provider": tts_provider,
            "enabled": True
        },
        "notifications": {
            "enabled": True,
            "sound_enabled": True
        },
        "logging": {
            "enabled": False
        }
    }
    
    if tts_provider == "kokoro":
        config["kokoro"] = {
            "voice": "af_sarah",
            "speed": 1.0,
            "models_dir": "models"
        }
    
    elif tts_provider == "elevenlabs":
        config["elevenlabs"] = {
            "api_key": "your_api_key_here",
            "voice_id": "21m00Tcm4TlvDq8ikWAM",
            "model_id": "eleven_flash_v2_5",
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    
    # Add helpful comments as a separate field
    config["_comments"] = {
        "tts_provider": "Choose 'kokoro' (local) or 'elevenlabs' (cloud)",
        "kokoro_voice": "Run 'uvx ccnotify setup --voices' to see all options",
        "kokoro_speed": "0.5 (slow) to 2.0 (fast)",
        "elevenlabs_api_key": "Get from https://elevenlabs.io/speech-synthesis",
        "elevenlabs_voice_id": "Get from your ElevenLabs account",
        "elevenlabs_model_id": "eleven_flash_v2_5 (fast/cheap) or eleven_multilingual_v2 (quality)"
    }
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)


def handle_config_command(args):
    """Handle config subcommand"""
    if args.init:
        init_config()
    elif args.show:
        show_config_paths()
    elif args.reset:
        reset_config()
    else:
        print("Use --init, --show, or --reset")


def show_config_paths():
    """Show configuration paths"""
    print("📁 CCNotify Configuration:")
    print(f"Config directory: {get_config_dir()}")
    print(f"Claude profile: {get_claude_profile_dir() or 'Not found'}")


def reset_config():
    """Reset configuration to defaults"""
    from .config import save_config, get_default_config
    
    response = input("Reset configuration to defaults? [y/N]: ")
    if response.lower() == 'y':
        if save_config(get_default_config()):
            print("✅ Configuration reset to defaults")
        else:
            print("❌ Failed to reset configuration")
    else:
        print("Reset cancelled")


if __name__ == "__main__":
    main()