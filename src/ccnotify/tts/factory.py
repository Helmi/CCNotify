"""
TTS provider factory - Creates and manages TTS provider instances
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, Type
import logging

from .base import TTSProvider, TTSProviderNotAvailable
from .kokoro import KokoroProvider
from .elevenlabs import ElevenLabsProvider

logger = logging.getLogger(__name__)


# Registry of available TTS providers
TTS_PROVIDERS: Dict[str, Type[TTSProvider]] = {
    "kokoro": KokoroProvider,
    "elevenlabs": ElevenLabsProvider,
}


def get_tts_provider(
    provider_name: str = None, config: Dict[str, Any] = None, fallback: bool = True
) -> Optional[TTSProvider]:
    """
    Get a TTS provider instance

    Args:
        provider_name: Name of the TTS provider to use
        config: Configuration dictionary for the provider
        fallback: Whether to try fallback providers if primary fails

    Returns:
        TTS provider instance, or None if no provider available
    """
    if config is None:
        config = {}

    # Get provider name from config or environment
    if provider_name is None:
        provider_name = config.get("provider", os.getenv("TTS_PROVIDER", "kokoro"))

    # Normalize provider name
    provider_name = provider_name.lower().strip()

    # Try primary provider
    provider = _create_provider(provider_name, config)
    if provider and provider.is_available():
        logger.info(f"Using TTS provider: {provider_name}")
        return provider

    if not fallback:
        return None

    # Try fallback providers
    fallback_order = _get_fallback_order(provider_name)

    for fallback_name in fallback_order:
        if fallback_name == provider_name:
            continue  # Skip the primary provider we already tried

        provider = _create_provider(fallback_name, config)
        if provider and provider.is_available():
            logger.info(f"Using fallback TTS provider: {fallback_name}")
            return provider

    logger.warning("No TTS providers available")
    return None


def _create_provider(provider_name: str, config: Dict[str, Any]) -> Optional[TTSProvider]:
    """Create a TTS provider instance"""
    try:
        if provider_name not in TTS_PROVIDERS:
            logger.error(f"Unknown TTS provider: {provider_name}")
            return None

        provider_class = TTS_PROVIDERS[provider_name]
        provider_config = _build_provider_config(provider_name, config)

        return provider_class(provider_config)

    except Exception as e:
        logger.error(f"Failed to create {provider_name} provider: {e}")
        return None


def _build_provider_config(provider_name: str, base_config: Dict[str, Any]) -> Dict[str, Any]:
    """Build configuration for a specific provider"""
    config = base_config.copy()

    if provider_name == "kokoro":
        config.update(
            {
                "models_dir": base_config.get("models_dir", "models"),
                "voice": os.getenv("KOKORO_VOICE", base_config.get("voice", "af_heart")),
                "speed": os.getenv("KOKORO_SPEED", base_config.get("speed", "1.0")),
                "format": os.getenv("KOKORO_FORMAT", base_config.get("format", "mp3")),
                "mp3_bitrate": os.getenv(
                    "KOKORO_MP3_BITRATE", base_config.get("mp3_bitrate", "128k")
                ),
            }
        )

    elif provider_name == "elevenlabs":
        config.update(
            {
                "api_key": os.getenv("ELEVENLABS_API_KEY", base_config.get("api_key", "")),
                "voice_id": os.getenv(
                    "ELEVENLABS_VOICE_ID", base_config.get("voice_id", "21m00Tcm4TlvDq8ikWAM")
                ),
                "model_id": os.getenv(
                    "ELEVENLABS_MODEL_ID", base_config.get("model_id", "eleven_flash_v2_5")
                ),
                "stability": base_config.get("stability", 0.5),
                "similarity_boost": base_config.get("similarity_boost", 0.5),
            }
        )

    return config


def _get_fallback_order(primary_provider: str) -> list:
    """Get fallback order based on primary provider preference"""

    # Define fallback preferences
    fallback_map = {
        "kokoro": ["elevenlabs"],
        "elevenlabs": ["kokoro"],
    }

    return fallback_map.get(primary_provider, ["kokoro", "elevenlabs"])


def list_available_providers() -> Dict[str, Dict[str, Any]]:
    """
    List all available TTS providers and their status

    Returns:
        Dictionary mapping provider names to their availability info
    """
    providers_info = {}

    for provider_name in TTS_PROVIDERS.keys():
        try:
            provider = _create_provider(provider_name, {})
            if provider:
                providers_info[provider_name] = {
                    "available": provider.is_available(),
                    "class": provider.__class__.__name__,
                    "extension": provider.get_file_extension(),
                    "description": _get_provider_description(provider_name),
                }
            else:
                providers_info[provider_name] = {
                    "available": False,
                    "error": "Failed to create provider",
                }

        except Exception as e:
            providers_info[provider_name] = {"available": False, "error": str(e)}

    return providers_info


def _get_provider_description(provider_name: str) -> str:
    """Get human-readable description of a provider"""
    descriptions = {
        "kokoro": "Local high-quality TTS using ONNX models",
        "elevenlabs": "Premium cloud-based TTS with natural voices",
    }
    return descriptions.get(provider_name, "Unknown provider")


def test_all_providers(test_text: str = "Hello, this is a TTS test") -> Dict[str, bool]:
    """
    Test all available providers

    Args:
        test_text: Text to use for testing

    Returns:
        Dictionary mapping provider names to test results
    """
    results = {}

    for provider_name in TTS_PROVIDERS.keys():
        try:
            provider = get_tts_provider(provider_name, fallback=False)
            if provider:
                # Test with a temporary file
                from tempfile import NamedTemporaryFile

                with NamedTemporaryFile(
                    suffix=provider.get_file_extension(), delete=False
                ) as tmp_file:
                    tmp_path = Path(tmp_file.name)

                success = provider.generate(test_text, tmp_path)

                # Clean up
                if tmp_path.exists():
                    tmp_path.unlink()

                results[provider_name] = success
            else:
                results[provider_name] = False

        except Exception as e:
            logger.error(f"Test failed for {provider_name}: {e}")
            results[provider_name] = False

    return results
