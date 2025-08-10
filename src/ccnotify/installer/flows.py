"""Installation and update flows for CCNotify."""

import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .detector import InstallationDetector, InstallationStatus
from .updater import UpdateManager, UpdateInfo
from .welcome import (
    display_welcome_screen,
    display_success_message,
    display_error_message,
    display_warning_message,
    display_progress_header,
    animate_thinking,
)
from ..config import get_claude_config_dir
from ..setup import setup_kokoro

console = Console()


class BaseFlow:
    """Base class for installation flows."""

    def __init__(self):
        self.detector = InstallationDetector()
        self.updater = UpdateManager()
        self.claude_dir = get_claude_config_dir()
        self.ccnotify_dir = self.claude_dir / "ccnotify"

    def _setup_kokoro(self) -> Optional[Dict[str, Any]]:
        """Setup Kokoro TTS provider."""
        console.print("\n[bold cyan]Setting up Kokoro TTS...[/bold cyan]")

        try:
            # Change to ccnotify directory so models are created in the right place
            import os

            original_cwd = os.getcwd()
            os.chdir(str(self.ccnotify_dir))

            try:
                # Call the existing setup_kokoro function
                setup_result = setup_kokoro(force_download=False)

                if setup_result:
                    # Include enhanced Kokoro configuration
                    return {
                        "tts_provider": "kokoro",
                        "models_downloaded": True,
                        "models_dir": str(self.ccnotify_dir / "models"),
                        "voice": "af_heart",  # Popular voices: af_heart, af_sarah, am_adam, af_sky, am_michael
                        "speed": 1.0,  # 0.5 = slower, 2.0 = faster
                        "format": "mp3",  # mp3 for smaller files, wav for quality, aiff for Mac compatibility
                        "mp3_bitrate": "128k",  # For MP3 encoding quality
                    }
                else:
                    console.print(f"[red]Failed to download Kokoro models[/red]")
                    return None
            finally:
                # Always restore original directory
                os.chdir(original_cwd)

        except Exception as e:
            console.print(f"[red]Error setting up Kokoro: {e}[/red]")
            return None

    def _configure_claude_hooks(self, logging: bool = False) -> bool:
        """Configure Claude hooks to use ccnotify."""
        from ..cli import update_claude_settings

        script_path = self.ccnotify_dir / "ccnotify.py"
        return update_claude_settings(str(script_path), logging=logging)


class FirstTimeFlow(BaseFlow):
    """Handles first-time installation flow."""

    def run(self, force: bool = False, quiet: bool = False, logging: bool = False) -> bool:
        """Execute first-time installation flow."""
        try:
            if not quiet:
                # Display welcome screen
                version = self.updater.get_current_package_version()
                platform_info = self.detector.get_platform_info()
                display_welcome_screen(version, platform_info["system"], is_update=False)

            # Check for existing installation
            status = self.detector.check_existing_installation()
            if status.exists and not force:
                if not quiet:
                    display_warning_message(
                        "CCNotify is already installed. Use 'uvx ccnotify install --force' to reinstall."
                    )
                return False

            # Step 1: Platform check
            if not quiet:
                display_progress_header("Platform Compatibility Check", 1, 5)
                animate_thinking("Checking platform compatibility")

            if not self._check_platform_compatibility(quiet):
                if not quiet:
                    display_error_message("Platform not supported")
                return False

            # Step 2: Migration check
            if self.detector.needs_migration():
                if not quiet:
                    display_progress_header("Legacy Installation Migration", 2, 5)

                if not self._handle_migration():
                    display_error_message("Failed to migrate legacy installation")
                    return False

            # Step 3: TTS Provider setup
            if not quiet:
                display_progress_header("TTS Provider Configuration", 3, 5)

            provider_config = self._setup_tts_provider(quiet)
            if not provider_config:
                display_error_message("TTS provider setup failed")
                return False

            # Step 4: Install script and configuration
            if not quiet:
                display_progress_header("Installing CCNotify Script", 4, 5)
                animate_thinking("Installing script and configuration")

            if not self._install_script_and_config(provider_config):
                display_error_message("Failed to install script and configuration")
                return False

            # Step 5: Configure Claude hooks
            if not quiet:
                display_progress_header("Configuring Claude Integration", 5, 5)
                animate_thinking("Updating Claude settings")

            if not self._configure_claude_hooks(logging=logging):
                display_error_message("Failed to configure Claude hooks")
                return False

            # Success message
            if not quiet:
                self._display_installation_success()

            return True

        except KeyboardInterrupt:
            if not quiet:
                display_warning_message("Installation cancelled by user")
            return False
        except Exception as e:
            if not quiet:
                display_error_message("Installation failed", str(e))
            return False

    def _check_platform_compatibility(self, quiet: bool = False) -> bool:
        """Check if current platform is supported."""
        platform_info = self.detector.get_platform_info()

        # Currently only macOS is fully supported
        if platform_info["system"] != "Darwin":
            if quiet:
                # In quiet mode, just proceed with installation on non-macOS systems
                return True
            else:
                console.print("[yellow]Warning: Full functionality only tested on macOS[/yellow]")
                if not Confirm.ask("Continue anyway?"):
                    return False

        return True

    def _handle_migration(self) -> bool:
        """Handle migration from legacy installation."""
        migration_info = self.detector.get_migration_info()

        console.print(
            f"[yellow]Found legacy installation in {migration_info['legacy_dir']}[/yellow]"
        )
        console.print("Files to migrate:")

        for file_name in migration_info["files_to_migrate"]:
            console.print(f"  • {file_name}")

        if not Confirm.ask("Migrate these files to the new location?"):
            return False

        return self.updater.migrate_legacy_installation()

    def _setup_tts_provider(self, quiet: bool = False) -> Optional[Dict[str, Any]]:
        """Setup TTS provider with user interaction."""
        if quiet:
            # Default to Kokoro in quiet mode with enhanced config
            return {
                "tts_provider": "kokoro",
                "voice": "af_heart",
                "speed": 1.0,
                "format": "mp3",
                "mp3_bitrate": "128k",
            }

        # Show provider options
        table = Table(title="TTS Provider Options")
        table.add_column("Option", style="cyan")
        table.add_column("Provider", style="bold")
        table.add_column("Description", style="dim")

        table.add_row("1", "Kokoro", "Local AI models (recommended, privacy-focused)")
        table.add_row("2", "ElevenLabs", "Cloud-based premium quality (requires API key)")
        table.add_row("3", "None", "Silent mode (no voice notifications)")

        console.print(table)
        console.print()

        while True:
            choice = Prompt.ask("Select TTS provider", choices=["1", "2", "3"], default="1")

            if choice == "1":
                # Kokoro setup
                if Confirm.ask("Download Kokoro TTS models? (~500MB)", default=True):
                    kokoro_config = self._setup_kokoro()
                    if not kokoro_config:
                        console.print(
                            "[yellow]Kokoro setup failed. Please choose another provider.[/yellow]"
                        )
                        continue
                    return kokoro_config
                else:
                    console.print(
                        "[yellow]Kokoro requires model files to function. Please choose another provider.[/yellow]"
                    )
                    continue

            elif choice == "2":
                # ElevenLabs setup
                elevenlabs_config = self._setup_elevenlabs()
                if not elevenlabs_config:
                    console.print(
                        "[yellow]ElevenLabs setup failed. Please choose another provider.[/yellow]"
                    )
                    continue
                return elevenlabs_config

            elif choice == "3":
                # Silent mode
                return {"tts_provider": "none"}

    def _setup_elevenlabs(self) -> Optional[Dict[str, Any]]:
        """Setup ElevenLabs TTS provider."""
        console.print("\n[bold cyan]Setting up ElevenLabs TTS...[/bold cyan]")

        api_key = Prompt.ask("Enter your ElevenLabs API key", password=True)
        if not api_key:
            console.print("[red]API key required for ElevenLabs[/red]")
            return None

        # TODO: Validate API key
        return {"tts_provider": "elevenlabs", "elevenlabs_api_key": api_key}

    def _install_script_and_config(self, provider_config: Dict[str, Any]) -> bool:
        """Install ccnotify.py script and configuration."""
        try:
            # Create ccnotify directory
            self.ccnotify_dir.mkdir(exist_ok=True)

            # Generate ccnotify.py script using existing template system
            from ..cli import get_notify_template

            script_content = get_notify_template()

            script_file = self.ccnotify_dir / "ccnotify.py"
            script_file.write_text(script_content)
            script_file.chmod(0o755)

            # Create configuration file
            config = {"config_version": "1.0", **provider_config}

            config_file = self.ccnotify_dir / "config.json"
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)

            return True
        except Exception:
            return False

    def _display_installation_success(self) -> None:
        """Display installation success message."""
        success_text = Text()
        success_text.append("CCNotify has been successfully installed!\n\n", style="bold green")
        success_text.append(
            "🔊 Voice notifications are now active for Claude Code\n", style="green"
        )
        success_text.append(
            "🎯 Try running commands in Claude Code to test notifications\n", style="green"
        )
        success_text.append("⚙️  Configuration stored in: ~/.claude/ccnotify/", style="dim")

        panel = Panel(
            success_text,
            title="[bold green]Installation Complete[/bold green]",
            border_style="green",
        )
        console.print(panel)


class UpdateFlow(BaseFlow):
    """Handles update flow for existing installations."""

    def run(self, config_only: bool = False, quiet: bool = False, logging: bool = False) -> bool:
        """Execute update flow."""
        try:
            # Check existing installation
            status = self.detector.check_existing_installation()

            if not status.exists:
                if not quiet:
                    display_error_message("No existing CCNotify installation found")
                return False

            if not quiet:
                # Display welcome screen
                version = self.updater.get_current_package_version()
                platform_info = self.detector.get_platform_info()
                display_welcome_screen(version, platform_info["system"], is_update=True)

            # Check for updates
            update_info = self.updater.check_for_updates(status)

            if not quiet:
                self._display_installation_status(status, update_info)

            # Check if there are no updates AND no issues
            if not self._has_updates(update_info) and not status.issues and not config_only:
                if not quiet:
                    display_success_message("CCNotify is already up to date!")
                return True

            # Show update options
            if not quiet and not config_only:
                if not self._confirm_updates(update_info, status):
                    display_warning_message("Update cancelled by user")
                    return False

            # Perform updates
            if not quiet:
                if update_info.script_update_available or update_info.config_migration_needed:
                    display_progress_header("Updating CCNotify", 1, 1)
                    animate_thinking("Applying updates")
                elif status.issues:
                    display_progress_header("Fixing Installation Issues", 1, 1)
                    animate_thinking("Resolving issues")

            # Create backup
            backup_paths = self.updater.create_backup()

            try:
                success = True

                if config_only:
                    success = self._update_config_only()
                else:
                    if update_info.script_update_available:
                        if not quiet:
                            display_progress_header("Updating CCNotify Script", 1, 1)
                        success = self.updater.update_script_only(preserve_config=True)

                    if success and update_info.config_migration_needed:
                        if not quiet:
                            display_progress_header("Migrating Configuration", 1, 1)
                        success = self._migrate_config()

                    # Fix missing models if needed
                    if success and status.issues:
                        for issue in status.issues:
                            if (
                                "models directory missing" in issue
                                and status.tts_provider == "kokoro"
                            ):
                                if not quiet:
                                    display_progress_header(
                                        "Downloading Missing Kokoro Models", 1, 1
                                    )

                                # Download models
                                kokoro_config = self._setup_kokoro()
                                if kokoro_config:
                                    # Update config with models_dir
                                    config_file = self.ccnotify_dir / "config.json"
                                    if config_file.exists():
                                        try:
                                            with open(config_file) as f:
                                                config = json.load(f)
                                            config.update(kokoro_config)
                                            with open(config_file, "w") as f:
                                                json.dump(config, f, indent=2)
                                        except Exception:
                                            pass

                            elif "not configured in Claude settings" in issue:
                                if not quiet:
                                    display_progress_header("Configuring Claude Integration", 1, 1)
                                self._configure_claude_hooks(logging=logging)

                if success:
                    # Clean up backups
                    self.updater.cleanup_backups(backup_paths)

                    if not quiet:
                        if (
                            update_info.script_update_available
                            or update_info.config_migration_needed
                        ):
                            display_success_message("CCNotify updated successfully!")
                        elif status.issues:
                            display_success_message("Installation issues resolved successfully!")
                        else:
                            display_success_message("CCNotify updated successfully!")
                else:
                    # Restore from backup
                    self.updater.restore_from_backup(backup_paths)
                    if not quiet:
                        display_error_message("Update failed, restored from backup")

                return success

            except Exception as e:
                # Restore from backup on error
                self.updater.restore_from_backup(backup_paths)
                if not quiet:
                    display_error_message("Update failed", str(e))
                return False

        except KeyboardInterrupt:
            if not quiet:
                display_warning_message("Update cancelled by user")
            return False
        except Exception as e:
            if not quiet:
                display_error_message("Update failed", str(e))
            return False

    def _display_installation_status(
        self, status: InstallationStatus, update_info: UpdateInfo
    ) -> None:
        """Display current installation status."""
        table = Table(title="Current Installation Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Version/Details", style="dim")

        # Script status
        script_status = "✓ Installed" if status.script_version else "✗ Missing"
        table.add_row("Script", script_status, status.script_version or "N/A")

        # TTS Provider
        provider_status = "✓ Configured" if status.tts_provider else "✗ Not configured"
        table.add_row("TTS Provider", provider_status, status.tts_provider or "N/A")

        # Models
        models_status = "✓ Downloaded" if status.models_downloaded else "✗ Missing"
        table.add_row("TTS Models", models_status, "")

        # Hooks
        hooks_status = "✓ Configured" if status.hooks_configured else "✗ Not configured"
        table.add_row("Claude Hooks", hooks_status, "")

        console.print(table)
        console.print()

        # Show issues if any
        if status.issues:
            console.print("[bold red]Issues found:[/bold red]")
            for issue in status.issues:
                console.print(f"  • [red]{issue}[/red]")
            console.print()

        # Show available updates
        if update_info.recommended_actions:
            console.print("[bold cyan]Available updates:[/bold cyan]")
            for action in update_info.recommended_actions:
                console.print(f"  • [cyan]{action}[/cyan]")
            console.print()

    def _has_updates(self, update_info: UpdateInfo) -> bool:
        """Check if any updates are available."""
        return (
            update_info.script_update_available
            or update_info.config_migration_needed
            or update_info.model_update_available
        )

    def _confirm_updates(self, update_info: UpdateInfo, status: InstallationStatus = None) -> bool:
        """Confirm with user which updates to apply."""
        actions_to_apply = []

        # Add version updates
        if update_info.recommended_actions:
            actions_to_apply.extend(update_info.recommended_actions)

        # Add issue fixes
        if status and status.issues:
            for issue in status.issues:
                if "models directory missing" in issue:
                    actions_to_apply.append("Download missing Kokoro models")
                elif "not configured in Claude settings" in issue:
                    actions_to_apply.append("Configure Claude hooks")

        if not actions_to_apply:
            return True

        console.print("[bold]The following updates will be applied:[/bold]")
        for action in actions_to_apply:
            console.print(f"  • {action}")

        return Confirm.ask("\nProceed with these updates?")

    def _update_config_only(self) -> bool:
        """Update only configuration without touching script."""
        # This would re-run the configuration setup
        return True

    def _migrate_config(self) -> bool:
        """Migrate configuration to newer format."""
        # This would handle config format migrations
        return True
