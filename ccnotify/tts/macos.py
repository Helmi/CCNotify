"""
macOS TTS provider - Built-in system text-to-speech
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, Any
import logging

from .base import TTSProvider, TTSProviderNotAvailable, TTSGenerationError

logger = logging.getLogger(__name__)


class MacOSProvider(TTSProvider):
    """macOS system TTS provider using the 'say' command"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Configuration
        self.voice = config.get("voice", "Samantha")
        self.rate = config.get("rate", None)  # Words per minute
        
        # Available system voices (commonly available)
        self.system_voices = {
            "female": ["Samantha", "Victoria", "Allison", "Ava", "Susan", "Tessa"],
            "male": ["Alex", "Tom", "Daniel", "Oliver", "Aaron", "Fred"],
            "novelty": ["Boing", "Bubbles", "Cellos", "Deranged", "Junior", "Ralph"]
        }
    
    def is_available(self) -> bool:
        """Check if macOS TTS is available"""
        # Only available on macOS
        if sys.platform != "darwin":
            return False
        
        try:
            # Test if 'say' command exists and works
            result = subprocess.run(
                ["say", "-v", "?"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False
    
    def generate(self, text: str, output_path: Path, **kwargs) -> bool:
        """
        Generate TTS audio using macOS 'say' command
        
        Args:
            text: Text to convert to speech
            output_path: Path where audio file should be saved
            **kwargs: Additional options (voice, rate)
        
        Returns:
            True if generation was successful, False otherwise
        """
        try:
            if not self.is_available():
                raise TTSProviderNotAvailable("macOS TTS is not available")
            
            # Get generation parameters
            voice = kwargs.get("voice", self.voice)
            rate = kwargs.get("rate", self.rate)
            
            # Build command
            cmd = [
                "say",
                "-o", str(output_path),
                "--file-format=AIFF",
                "-v", voice
            ]
            
            # Add rate if specified
            if rate:
                cmd.extend(["-r", str(rate)])
            
            # Add text
            cmd.append(text)
            
            self.logger.debug(f"Generating TTS: '{text[:50]}...' with voice={voice}")
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Run the say command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                error_msg = f"macOS 'say' command failed: {result.stderr}"
                raise TTSGenerationError(error_msg)
            
            # Verify output file was created
            if not output_path.exists() or output_path.stat().st_size == 0:
                raise TTSGenerationError("Output file was not created or is empty")
            
            self.log_generation(text, output_path, True, voice=voice, rate=rate)
            return True
        
        except Exception as e:
            self.logger.error(f"macOS TTS generation failed: {e}")
            self.log_generation(text, output_path, False)
            
            # Clean up partial file
            if output_path.exists():
                try:
                    output_path.unlink()
                except:
                    pass
            
            return False
    
    def get_file_extension(self) -> str:
        """Get the file extension for macOS TTS audio files"""
        return ".aiff"
    
    def get_available_voices(self) -> Dict[str, list]:
        """
        Get list of available system voices
        
        Returns:
            Dictionary mapping voice categories to voice lists
        """
        try:
            if not self.is_available():
                return self.system_voices  # Return default list
            
            # Get actual system voices
            result = subprocess.run(
                ["say", "-v", "?"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return self.system_voices
            
            # Parse voice list
            voices = {"system": [], "female": [], "male": [], "other": []}
            
            for line in result.stdout.split('\n'):
                if line.strip():
                    # Extract voice name (first word)
                    parts = line.strip().split()
                    if parts:
                        voice_name = parts[0]
                        
                        # Categorize voice
                        if voice_name in self.system_voices["female"]:
                            voices["female"].append(voice_name)
                        elif voice_name in self.system_voices["male"]:
                            voices["male"].append(voice_name)
                        elif voice_name in self.system_voices["novelty"]:
                            voices["other"].append(voice_name)
                        else:
                            voices["system"].append(voice_name)
            
            return voices
        
        except Exception as e:
            self.logger.error(f"Error fetching available voices: {e}")
            return self.system_voices
    
    def test_voice(self, voice: str, test_text: str = "Hello, this is a test of macOS TTS") -> bool:
        """
        Test a specific voice by generating a sample
        
        Args:
            voice: macOS voice name to test
            test_text: Text to use for testing
        
        Returns:
            True if voice test successful, False otherwise
        """
        try:
            from tempfile import NamedTemporaryFile
            
            with NamedTemporaryFile(suffix=".aiff", delete=False) as tmp_file:
                tmp_path = Path(tmp_file.name)
            
            success = self.generate(test_text, tmp_path, voice=voice)
            
            # Clean up test file
            if tmp_path.exists():
                tmp_path.unlink()
            
            return success
        
        except Exception as e:
            self.logger.error(f"Voice test failed for {voice}: {e}")
            return False
    
    def get_voice_info(self, voice: str) -> Dict[str, Any]:
        """
        Get information about a specific voice
        
        Args:
            voice: macOS voice name
        
        Returns:
            Dictionary containing voice information
        """
        try:
            if not self.is_available():
                return {}
            
            # Get detailed voice information
            result = subprocess.run(
                ["say", "-v", voice, "-?"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return {
                    "name": voice,
                    "platform": "macOS",
                    "type": "system",
                    "description": result.stdout.strip()
                }
            else:
                return {"name": voice, "platform": "macOS", "type": "system"}
        
        except Exception as e:
            self.logger.error(f"Error getting voice info for {voice}: {e}")
            return {"name": voice, "platform": "macOS", "type": "system"}