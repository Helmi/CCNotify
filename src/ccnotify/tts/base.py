"""
Base TTS provider interface
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class TTSProvider(ABC):
    """Abstract base class for TTS providers"""

    def __init__(self, config: Dict[str, Any]):
        """Initialize TTS provider with configuration"""
        self.config = config
        self.logger = logger.getChild(self.__class__.__name__)

    @abstractmethod
    def is_available(self) -> bool:
        """Check if TTS provider is available and properly configured"""
        pass

    @abstractmethod
    def generate(self, text: str, output_path: Path, **kwargs) -> bool:
        """
        Generate TTS audio from text

        Args:
            text: Text to convert to speech
            output_path: Path where audio file should be saved
            **kwargs: Provider-specific options (voice, speed, etc.)

        Returns:
            True if generation was successful, False otherwise
        """
        pass

    @abstractmethod
    def get_file_extension(self) -> str:
        """Get the file extension for audio files produced by this provider"""
        pass

    def get_cache_key(self, text: str, **kwargs) -> str:
        """
        Generate a cache key for the given text and options

        Args:
            text: Text to convert to speech
            **kwargs: Provider-specific options

        Returns:
            Cache key string
        """
        import hashlib

        # Create a string representation of all parameters
        cache_data = f"{text}|{sorted(kwargs.items())}"

        # Generate a hash for the cache key
        return hashlib.md5(cache_data.encode()).hexdigest()[:8]

    def validate_config(self, required_keys: list) -> bool:
        """
        Validate that required configuration keys are present

        Args:
            required_keys: List of required configuration keys

        Returns:
            True if all required keys are present, False otherwise
        """
        for key in required_keys:
            if key not in self.config or not self.config[key]:
                self.logger.error(f"Missing required configuration key: {key}")
                return False
        return True

    def log_generation(self, text: str, output_path: Path, success: bool, **kwargs):
        """Log TTS generation attempt"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(
            f"TTS generation {status}: '{text[:50]}...' -> {output_path.name} "
            f"({self.__class__.__name__})"
        )

        if kwargs:
            self.logger.debug(f"Generation options: {kwargs}")


class TTSError(Exception):
    """Base exception for TTS-related errors"""

    pass


class TTSProviderNotAvailable(TTSError):
    """Raised when a TTS provider is not available"""

    pass


class TTSGenerationError(TTSError):
    """Raised when TTS generation fails"""

    pass
