"""
ElevenLabs TTS provider - Premium cloud-based text-to-speech
"""

from pathlib import Path
from typing import Dict, Any
import logging

# Import requests only when needed
try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from .base import TTSProvider, TTSProviderNotAvailable, TTSGenerationError

logger = logging.getLogger(__name__)


class ElevenLabsProvider(TTSProvider):
    """ElevenLabs TTS provider using cloud API"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Configuration
        self.api_key = config.get("api_key", "")
        self.voice_id = config.get("voice_id", "21m00Tcm4TlvDq8ikWAM")  # Rachel
        self.model_id = config.get("model_id", "eleven_flash_v2_5")

        # API settings
        self.base_url = "https://api.elevenlabs.io/v1"
        self.timeout = config.get("timeout", 30)

        # Voice settings
        self.stability = float(config.get("stability", 0.5))
        self.similarity_boost = float(config.get("similarity_boost", 0.5))

    def is_available(self) -> bool:
        """Check if ElevenLabs TTS is available"""
        if not REQUESTS_AVAILABLE:
            self.logger.warning("requests library not installed - needed for ElevenLabs")
            return False

        if not self.api_key:
            self.logger.warning("ElevenLabs API key not configured")
            return False

        try:
            # Test API connectivity
            response = requests.get(
                f"{self.base_url}/voices", headers={"xi-api-key": self.api_key}, timeout=5
            )

            if response.status_code == 200:
                return True
            elif response.status_code == 401:
                self.logger.error("ElevenLabs API key invalid")
                return False
            else:
                self.logger.warning(f"ElevenLabs API returned status {response.status_code}")
                return False

        except requests.RequestException as e:
            self.logger.warning(f"ElevenLabs API connectivity test failed: {e}")
            return False

    def generate(self, text: str, output_path: Path, **kwargs) -> bool:
        """
        Generate TTS audio using ElevenLabs API

        Args:
            text: Text to convert to speech
            output_path: Path where audio file should be saved
            **kwargs: Additional options (voice_id, model_id, stability, similarity_boost)

        Returns:
            True if generation was successful, False otherwise
        """
        try:
            if not self.is_available():
                raise TTSProviderNotAvailable("ElevenLabs TTS is not available")

            # Get generation parameters
            voice_id = kwargs.get("voice_id", self.voice_id)
            model_id = kwargs.get("model_id", self.model_id)
            stability = float(kwargs.get("stability", self.stability))
            similarity_boost = float(kwargs.get("similarity_boost", self.similarity_boost))

            # Prepare request
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            headers = {"xi-api-key": self.api_key, "Content-Type": "application/json"}

            payload = {
                "text": text,
                "model_id": model_id,
                "voice_settings": {"stability": stability, "similarity_boost": similarity_boost},
            }

            self.logger.debug(
                f"Generating TTS: '{text[:50]}...' with voice={voice_id}, model={model_id}"
            )

            # Make API request
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)

            # Check response
            if response.status_code != 200:
                error_msg = f"ElevenLabs API error {response.status_code}"
                try:
                    error_detail = response.json().get("detail", "")
                    if error_detail:
                        error_msg += f": {error_detail}"
                except:
                    pass

                raise TTSGenerationError(error_msg)

            # Save audio data
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(response.content)

            self.log_generation(text, output_path, True, voice_id=voice_id, model_id=model_id)
            return True

        except Exception as e:
            self.logger.error(f"ElevenLabs TTS generation failed: {e}")
            self.log_generation(text, output_path, False)

            # Clean up partial file
            if output_path.exists():
                try:
                    output_path.unlink()
                except:
                    pass

            return False

    def get_file_extension(self) -> str:
        """Get the file extension for ElevenLabs audio files"""
        return ".mp3"

    def get_available_voices(self) -> Dict[str, Any]:
        """
        Get list of available voices from ElevenLabs API

        Returns:
            Dictionary containing voice information
        """
        try:
            if not self.is_available():
                return {}

            response = requests.get(
                f"{self.base_url}/voices",
                headers={"xi-api-key": self.api_key},
                timeout=self.timeout,
            )

            if response.status_code == 200:
                voices_data = response.json()

                # Organize voices by category
                voices = {}
                for voice in voices_data.get("voices", []):
                    voice_info = {
                        "voice_id": voice.get("voice_id"),
                        "name": voice.get("name"),
                        "category": voice.get("category", "Unknown"),
                        "description": voice.get("description", ""),
                        "labels": voice.get("labels", {}),
                        "preview_url": voice.get("preview_url", ""),
                    }

                    category = voice_info["category"]
                    if category not in voices:
                        voices[category] = []
                    voices[category].append(voice_info)

                return voices
            else:
                self.logger.error(f"Failed to fetch voices: {response.status_code}")
                return {}

        except Exception as e:
            self.logger.error(f"Error fetching available voices: {e}")
            return {}

    def get_voice_info(self, voice_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific voice

        Args:
            voice_id: ElevenLabs voice ID

        Returns:
            Dictionary containing voice information
        """
        try:
            if not self.is_available():
                return {}

            response = requests.get(
                f"{self.base_url}/voices/{voice_id}",
                headers={"xi-api-key": self.api_key},
                timeout=self.timeout,
            )

            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to fetch voice info: {response.status_code}")
                return {}

        except Exception as e:
            self.logger.error(f"Error fetching voice info for {voice_id}: {e}")
            return {}

    def test_voice(
        self, voice_id: str, test_text: str = "Hello, this is a test of ElevenLabs TTS"
    ) -> bool:
        """
        Test a specific voice by generating a sample

        Args:
            voice_id: ElevenLabs voice ID to test
            test_text: Text to use for testing

        Returns:
            True if voice test successful, False otherwise
        """
        try:
            from tempfile import NamedTemporaryFile

            with NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
                tmp_path = Path(tmp_file.name)

            success = self.generate(test_text, tmp_path, voice_id=voice_id)

            # Clean up test file
            if tmp_path.exists():
                tmp_path.unlink()

            return success

        except Exception as e:
            self.logger.error(f"Voice test failed for {voice_id}: {e}")
            return False
