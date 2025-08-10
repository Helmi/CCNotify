"""
Kokoro TTS provider - Local, high-quality text-to-speech
"""

from pathlib import Path
from typing import Dict, Any, Optional
import logging

from .base import TTSProvider, TTSProviderNotAvailable, TTSGenerationError

logger = logging.getLogger(__name__)


class KokoroProvider(TTSProvider):
    """Kokoro TTS provider using local ONNX models"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._kokoro = None
        self._models_dir = Path(config.get("models_dir", "models"))

        # Default configuration with enhanced options
        self.voice = config.get(
            "voice", "af_heart"
        )  # Popular voices: af_heart, af_sarah, am_adam, af_sky, am_michael
        self.speed = float(config.get("speed", 1.0))  # 0.5 = slower, 2.0 = faster
        self.format = config.get("format", "mp3").lower()  # mp3, wav, or aiff
        self.mp3_bitrate = config.get("mp3_bitrate", "128k")  # For MP3 encoding

        # Model file paths
        self.model_path = self._models_dir / "kokoro-v1.0.onnx"
        self.voices_path = self._models_dir / "voices-v1.0.bin"

    def is_available(self) -> bool:
        """Check if Kokoro TTS is available"""
        try:
            # Check if model files exist
            if not self.model_path.exists():
                self.logger.warning(f"Kokoro model file not found: {self.model_path}")
                return False

            if not self.voices_path.exists():
                self.logger.warning(f"Kokoro voices file not found: {self.voices_path}")
                return False

            # Try to import and initialize Kokoro
            self._ensure_kokoro_loaded()
            return True

        except ImportError as e:
            self.logger.warning(f"Kokoro TTS not available: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Kokoro TTS availability check failed: {e}")
            return False

    def _ensure_kokoro_loaded(self):
        """Ensure Kokoro TTS is loaded and ready"""
        if self._kokoro is None:
            try:
                from kokoro_onnx import KokoroTTS

                self._kokoro = KokoroTTS(
                    model_path=str(self.model_path), voices_path=str(self.voices_path)
                )
                self.logger.info("Kokoro TTS initialized successfully")
            except ImportError:
                raise TTSProviderNotAvailable(
                    "kokoro-onnx package not installed. Install with: pip install kokoro-onnx"
                )
            except Exception as e:
                raise TTSProviderNotAvailable(f"Failed to initialize Kokoro TTS: {e}")

    def generate(self, text: str, output_path: Path, **kwargs) -> bool:
        """
        Generate TTS audio using Kokoro

        Args:
            text: Text to convert to speech
            output_path: Path where audio file should be saved
            **kwargs: Additional options (voice, speed)

        Returns:
            True if generation was successful, False otherwise
        """
        try:
            if not self.is_available():
                raise TTSProviderNotAvailable("Kokoro TTS is not available")

            # Get generation parameters
            voice = kwargs.get("voice", self.voice)
            speed = float(kwargs.get("speed", self.speed))

            # Validate voice format
            voice = self._validate_voice(voice)

            # Ensure Kokoro is loaded
            self._ensure_kokoro_loaded()

            # Generate audio
            self.logger.debug(f"Generating TTS: '{text[:50]}...' with voice={voice}, speed={speed}")

            # Generate the audio data (Kokoro generates WAV format)
            audio_data = self._kokoro.generate(text=text, voice=voice, speed=speed)

            # Save to file with format conversion if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Get desired format from config or output path extension
            target_format = self.format
            if output_path.suffix:
                # Use output path extension if specified
                target_format = output_path.suffix[1:].lower()

            if target_format in ["mp3", "aiff"] and target_format != "wav":
                # Convert WAV to target format using pydub
                self._save_with_conversion(audio_data, output_path, target_format)
            else:
                # Save as WAV directly
                with open(output_path, "wb") as f:
                    f.write(audio_data)

            self.log_generation(text, output_path, True, voice=voice, speed=speed)
            return True

        except Exception as e:
            self.logger.error(f"Kokoro TTS generation failed: {e}")
            self.log_generation(text, output_path, False, voice=voice, speed=speed)

            # Clean up partial file
            if output_path.exists():
                try:
                    output_path.unlink()
                except:
                    pass

            return False

    def get_file_extension(self) -> str:
        """Get the file extension for Kokoro audio files"""
        return f".{self.format}"

    def _save_with_conversion(self, audio_data: bytes, output_path: Path, format: str):
        """Convert WAV audio data to another format and save"""
        try:
            from pydub import AudioSegment
            import io

            # Load WAV data into AudioSegment
            audio = AudioSegment.from_wav(io.BytesIO(audio_data))

            # Export to desired format
            if format == "mp3":
                audio.export(output_path, format="mp3", bitrate=self.mp3_bitrate)
                self.logger.debug(f"Converted to MP3 with bitrate {self.mp3_bitrate}")
            elif format == "aiff":
                audio.export(output_path, format="aiff")
                self.logger.debug(f"Converted to AIFF")
            else:
                # Fallback to WAV
                with open(output_path, "wb") as f:
                    f.write(audio_data)
        except ImportError:
            # If pydub is not available, save as WAV
            self.logger.warning("pydub not available for format conversion, saving as WAV")
            with open(output_path, "wb") as f:
                f.write(audio_data)
        except Exception as e:
            self.logger.error(f"Format conversion failed: {e}, saving as WAV")
            with open(output_path, "wb") as f:
                f.write(audio_data)

    def _validate_voice(self, voice: str) -> str:
        """
        Validate and normalize voice parameter

        Args:
            voice: Voice specification (single voice or blended)

        Returns:
            Validated voice string
        """
        if not voice:
            return self.voice

        # Handle voice blending (e.g., "af_sarah:60,am_adam:40")
        if "," in voice:
            # Validate blended voice format
            voices = voice.split(",")
            normalized_voices = []

            for v in voices:
                if ":" in v:
                    voice_name, weight = v.strip().split(":")
                    try:
                        weight_val = float(weight)
                        if not 0 <= weight_val <= 100:
                            self.logger.warning(f"Voice weight {weight_val} out of range (0-100)")
                    except ValueError:
                        self.logger.warning(f"Invalid voice weight: {weight}")
                    normalized_voices.append(f"{voice_name.strip()}:{weight}")
                else:
                    normalized_voices.append(v.strip())

            return ",".join(normalized_voices)

        # Single voice
        return voice.strip()

    def get_available_voices(self) -> Dict[str, list]:
        """
        Get list of available voices organized by category

        Returns:
            Dictionary mapping voice categories to voice lists
        """
        return {
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

    def test_voice(
        self, voice: str, test_text: str = "Hello, this is a test of Kokoro TTS"
    ) -> bool:
        """
        Test a specific voice by generating a sample

        Args:
            voice: Voice to test
            test_text: Text to use for testing

        Returns:
            True if voice test successful, False otherwise
        """
        try:
            from tempfile import NamedTemporaryFile

            with NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_path = Path(tmp_file.name)

            success = self.generate(test_text, tmp_path, voice=voice)

            # Clean up test file
            if tmp_path.exists():
                tmp_path.unlink()

            return success

        except Exception as e:
            self.logger.error(f"Voice test failed for {voice}: {e}")
            return False
